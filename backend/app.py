from datetime import date
import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from db import get_connection


# ==================================================
# FLASK CONFIGURATION
# ==================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "railease-development-key-change-this"
)


# ==================================================
# DATABASE HELPER FUNCTIONS
# ==================================================

def fetch_all(query, params=()):
    """Fetch multiple database records."""

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, params)
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def fetch_one(query, params=()):
    """Fetch one database record."""

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, params)
        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def home():

    trains = fetch_all("""
        SELECT
            Train_ID,
            Train_Name,
            Source,
            Destination,
            Total_Seats,
            Available_Seats,
            Price_Per_Seat
        FROM Trains
        ORDER BY Train_ID
    """)

    return render_template(
        "index.html",
        trains=trains
    )


# ==================================================
# ROUTE ANALYSIS / SEARCH TRAINS
# ==================================================

@app.route("/routes")
def routes_page():

    source = request.args.get("source", "").strip()
    destination = request.args.get("destination", "").strip()
    travel_date = request.args.get("travel_date", "").strip()

    trains = []
    searched = False
    error = None

    if source or destination or travel_date:

        searched = True

        if not source or not destination or not travel_date:
            error = (
                "Please enter the source, destination "
                "and journey date."
            )

        elif source.casefold() == destination.casefold():
            error = "Source and destination must be different."

        else:
            try:
                selected_date = date.fromisoformat(travel_date)

                if selected_date < date.today():
                    error = (
                        "Please select today or a future "
                        "travel date."
                    )

                else:
                    trains = fetch_all("""
                        SELECT
                            T.Train_ID,
                            T.Train_Name,
                            T.Source,
                            T.Destination,
                            T.Total_Seats,
                            T.Price_Per_Seat,

                            T.Total_Seats - COALESCE(
                                (
                                    SELECT SUM(B.Seats_Booked)
                                    FROM Bookings B
                                    WHERE B.Train_ID = T.Train_ID
                                      AND B.Travel_Date = %s
                                      AND B.Booking_Status = 'Confirmed'
                                ),
                                0
                            ) AS Available_Seats

                        FROM Trains T

                        WHERE LOWER(T.Source) = LOWER(%s)
                          AND LOWER(T.Destination) = LOWER(%s)

                        HAVING Available_Seats > 0

                        ORDER BY T.Train_Name
                    """, (
                        selected_date,
                        source,
                        destination
                    ))

            except ValueError:
                error = "Please select a valid travel date."

    return render_template(
        "routes.html",
        trains=trains,
        source=source,
        destination=destination,
        travel_date=travel_date,
        today=date.today().isoformat(),
        searched=searched,
        error=error
    )


# ==================================================
# ALL TRAINS
# ==================================================

@app.route("/trains")
def trains_page():

    trains = fetch_all("""
        SELECT
            Train_ID,
            Train_Name,
            Source,
            Destination,
            Total_Seats,
            Available_Seats,
            Price_Per_Seat
        FROM Trains
        ORDER BY Train_ID
    """)

    route_counts = fetch_all("""
        SELECT
            Source,
            Destination,
            COUNT(*) AS Total_Trains
        FROM Trains
        GROUP BY Source, Destination
        ORDER BY Source, Destination
    """)

    return render_template(
        "trains.html",
        trains=trains,
        route_counts=route_counts
    )


# ==================================================
# BOOKING DETAILS
# ==================================================

@app.route("/bookings")
def bookings_page():

    bookings = fetch_all("""
        SELECT
            Booking_ID,
            Customer_Name,
            Phone,
            Train_Name,
            Source,
            Destination,
            Travel_Date,
            Seats_Booked,
            Total_Fare,
            Booking_Status
        FROM Booking_Details
        ORDER BY Booking_ID DESC
    """)

    return render_template(
        "bookings.html",
        bookings=bookings
    )


# ==================================================
# BOOK A TICKET
# ==================================================

@app.route("/book", methods=["GET", "POST"])
def book_page():

    # --------------------------------------------------
    # DISPLAY THE BOOKING FORM
    # --------------------------------------------------

    if request.method == "GET":

        trains = fetch_all("""
            SELECT
                Train_ID,
                Train_Name,
                Source,
                Destination,
                Total_Seats,
                Price_Per_Seat
            FROM Trains
            ORDER BY Train_Name
        """)

        return render_template(
            "book.html",
            trains=trains,
            today=date.today().isoformat()
        )

    # --------------------------------------------------
    # READ FORM DATA
    # --------------------------------------------------

    customer_name = request.form.get(
        "customer_name", ""
    ).strip()

    phone = request.form.get(
        "phone", ""
    ).strip()

    email = request.form.get(
        "email", ""
    ).strip()

    try:
        train_id = int(request.form.get("train_id", ""))
        seats = int(request.form.get("seats", ""))

        travel_date = date.fromisoformat(
            request.form.get("travel_date", "")
        )

    except (ValueError, TypeError):
        flash(
            "Please enter valid booking details.",
            "error"
        )
        return redirect(url_for("book_page"))

    if not customer_name or not phone:
        flash(
            "Customer name and phone are required.",
            "error"
        )
        return redirect(url_for("book_page"))

    if seats <= 0:
        flash(
            "Please book at least one seat.",
            "error"
        )
        return redirect(url_for("book_page"))

    if travel_date < date.today():
        flash(
            "You cannot book a ticket for a past date.",
            "error"
        )
        return redirect(url_for("book_page"))

    connection = None
    cursor = None

    try:
        connection = get_connection()
        connection.start_transaction()

        cursor = connection.cursor(dictionary=True)

        # --------------------------------------------------
        # STEP 1: FIND THE SELECTED TRAIN
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                Train_ID,
                Train_Name,
                Total_Seats,
                Price_Per_Seat
            FROM Trains
            WHERE Train_ID = %s
            FOR UPDATE
        """, (train_id,))

        train = cursor.fetchone()

        if not train:
            connection.rollback()

            flash(
                "The selected train was not found.",
                "error"
            )

            return redirect(url_for("book_page"))

        # --------------------------------------------------
        # STEP 2: CALCULATE AVAILABLE SEATS
        # FOR THE SELECTED TRAVEL DATE
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                COALESCE(SUM(Seats_Booked), 0) AS Booked_Seats
            FROM Bookings
            WHERE Train_ID = %s
              AND Travel_Date = %s
              AND Booking_Status = 'Confirmed'
        """, (train_id, travel_date))

        booked_seats = int(
            cursor.fetchone()["Booked_Seats"]
        )

        available_seats = (
            int(train["Total_Seats"]) - booked_seats
        )

        if seats > available_seats:
            connection.rollback()

            flash(
                f"Only {available_seats} seats are available "
                f"for this travel date.",
                "error"
            )

            return redirect(url_for("book_page"))

        # --------------------------------------------------
        # STEP 3: FIND OR CREATE THE CUSTOMER
        # --------------------------------------------------

        cursor.execute("""
            SELECT Customer_ID
            FROM Customers
            WHERE Phone = %s
            LIMIT 1
        """, (phone,))

        customer = cursor.fetchone()

        if customer:

            customer_id = customer["Customer_ID"]

        else:

            cursor.execute("""
                SELECT
                    COALESCE(MAX(Customer_ID), 0) + 1
                    AS Next_Customer_ID
                FROM Customers
            """)

            customer_id = cursor.fetchone()["Next_Customer_ID"]

            cursor.execute("""
                INSERT INTO Customers (
                    Customer_ID,
                    Customer_Name,
                    Phone,
                    Email
                )
                VALUES (%s, %s, %s, %s)
            """, (
                customer_id,
                customer_name,
                phone,
                email or None
            ))

        # --------------------------------------------------
        # STEP 4: GENERATE THE BOOKING ID
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                COALESCE(MAX(Booking_ID), 1000) + 1
                AS Next_Booking_ID
            FROM Bookings
        """)

        booking_id = cursor.fetchone()["Next_Booking_ID"]

        # --------------------------------------------------
        # STEP 5: CALCULATE THE TOTAL FARE
        # --------------------------------------------------

        total_fare = seats * train["Price_Per_Seat"]

        # --------------------------------------------------
        # STEP 6: INSERT THE BOOKING INTO MYSQL
        # --------------------------------------------------

        cursor.execute("""
            INSERT INTO Bookings (
                Booking_ID,
                Customer_ID,
                Train_ID,
                Travel_Date,
                Booking_Date,
                Seats_Booked,
                Total_Fare,
                Booking_Status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            booking_id,
            customer_id,
            train_id,
            travel_date,
            date.today(),
            seats,
            total_fare,
            "Confirmed"
        ))

        # Save the transaction permanently.
        connection.commit()

        flash(
            f"Booking successful! Booking ID: {booking_id}. "
            f"Total fare: ₹{total_fare:.2f}. "
            f"Status: Confirmed.",
            "success"
        )

        return redirect(url_for("bookings_page"))

    except Exception:

        if connection:
            connection.rollback()

        app.logger.exception("Booking operation failed")

        flash(
            "Booking failed. Please check the terminal "
            "for the error.",
            "error"
        )

        return redirect(url_for("book_page"))

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.route("/admin")
def admin_page():

    # --------------------------------------------------
    # QUERY 4:
    # CUSTOMERS WHO BOOKED MORE THAN 3 DISTINCT TRAINS
    # IN THE PREVIOUS 3 MONTHS
    # --------------------------------------------------

    frequent_customers = fetch_all("""
        SELECT
            C.Customer_ID,
            C.Customer_Name,
            COUNT(DISTINCT B.Train_ID) AS Total_Trains_Booked,
            COALESCE(SUM(B.Total_Fare), 0) AS Total_Revenue

        FROM Customers C

        INNER JOIN Bookings B
            ON C.Customer_ID = B.Customer_ID

        WHERE B.Booking_Date >=
              DATE_SUB(CURDATE(), INTERVAL 3 MONTH)

          AND B.Booking_Date < CURDATE()

          AND B.Booking_Status = 'Confirmed'

        GROUP BY
            C.Customer_ID,
            C.Customer_Name

        HAVING COUNT(DISTINCT B.Train_ID) > 3

        ORDER BY Total_Trains_Booked DESC
    """)

    # --------------------------------------------------
    # REVENUE FOR EVERY CUSTOMER
    # --------------------------------------------------

    customer_revenue = fetch_all("""
        SELECT
            C.Customer_ID,
            C.Customer_Name,

            COUNT(
                CASE
                    WHEN B.Booking_Status = 'Confirmed'
                    THEN B.Booking_ID
                END
            ) AS Total_Bookings,

            COALESCE(
                SUM(
                    CASE
                        WHEN B.Booking_Status = 'Confirmed'
                        THEN B.Seats_Booked
                        ELSE 0
                    END
                ),
                0
            ) AS Total_Seats_Booked,

            COALESCE(
                SUM(
                    CASE
                        WHEN B.Booking_Status = 'Confirmed'
                        THEN B.Total_Fare
                        ELSE 0
                    END
                ),
                0
            ) AS Total_Revenue

        FROM Customers C

        LEFT JOIN Bookings B
            ON C.Customer_ID = B.Customer_ID

        GROUP BY
            C.Customer_ID,
            C.Customer_Name

        ORDER BY Total_Revenue DESC, C.Customer_ID
    """)

    # --------------------------------------------------
    # QUERY 5:
    # TOP 3 TRAINS BY SEATS BOOKED IN OCTOBER 2026
    # WITH THEIR TOTAL REVENUE
    # --------------------------------------------------

    top_trains = fetch_all("""
        SELECT
            T.Train_ID,
            T.Train_Name,

            CONCAT(
                T.Source,
                ' → ',
                T.Destination
            ) AS Route,

            SUM(B.Seats_Booked) AS Total_Seats_Booked,
            SUM(B.Total_Fare) AS Total_Revenue

        FROM Trains T

        INNER JOIN Bookings B
            ON T.Train_ID = B.Train_ID

        WHERE B.Booking_Date >= '2026-10-01'
          AND B.Booking_Date < '2026-11-01'

          AND B.Booking_Status = 'Confirmed'

        GROUP BY
            T.Train_ID,
            T.Train_Name,
            T.Source,
            T.Destination

        ORDER BY
            Total_Seats_Booked DESC,
            T.Train_ID

        LIMIT 3
    """)

    # --------------------------------------------------
    # ALL BOOKINGS, INCLUDING FARE AND STATUS
    # --------------------------------------------------

    booking_revenue = fetch_all("""
        SELECT
            Booking_ID,
            Customer_Name,
            Phone,
            Train_Name,
            Source,
            Destination,
            Travel_Date,
            Seats_Booked,
            Total_Fare,
            Booking_Status

        FROM Booking_Details

        ORDER BY Booking_ID DESC
    """)

    # --------------------------------------------------
    # DASHBOARD SUMMARY CARDS
    # --------------------------------------------------

    summary = fetch_one("""
        SELECT
            (SELECT COUNT(*) FROM Trains)
                AS Total_Trains,

            (SELECT COUNT(*) FROM Customers)
                AS Total_Customers,

            (
                SELECT COUNT(*)
                FROM Bookings
                WHERE Booking_Status = 'Confirmed'
            ) AS Confirmed_Bookings,

            (
                SELECT COALESCE(SUM(Total_Fare), 0)
                FROM Bookings
                WHERE Booking_Status = 'Confirmed'
            ) AS Total_Revenue
    """)

    return render_template(
        "admin.html",
        frequent_customers=frequent_customers,
        customer_revenue=customer_revenue,
        top_trains=top_trains,
        booking_revenue=booking_revenue,
        summary=summary
    )


# ==================================================
# START FLASK
# ==================================================

if __name__ == "__main__":
    app.run(debug=True)