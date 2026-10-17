// ========================================
// 1. SAMPLE TRAIN DATA
// ========================================

// Temporary data for testing the frontend.
// Later, Flask will fetch trains from MySQL.

const trains = [
    {
        id: 1,
        number: "12985",
        name: "Double Decker Express",
        from: "Delhi",
        to: "Jaipur",
        departure: "06:00 AM",
        arrival: "10:30 AM",
        duration: "4h 30m",
        fare: 450,
        seats: 45
    },
    {
        id: 2,
        number: "12956",
        name: "Jaipur Superfast",
        from: "Delhi",
        to: "Jaipur",
        departure: "08:15 AM",
        arrival: "01:00 PM",
        duration: "4h 45m",
        fare: 520,
        seats: 32
    },
    {
        id: 3,
        number: "12951",
        name: "Rajdhani Express",
        from: "Delhi",
        to: "Mumbai",
        departure: "04:30 PM",
        arrival: "08:00 AM",
        duration: "15h 30m",
        fare: 1450,
        seats: 20
    },
    {
        id: 4,
        number: "12015",
        name: "Ajmer Shatabdi",
        from: "Jaipur",
        to: "Delhi",
        departure: "06:10 AM",
        arrival: "10:40 AM",
        duration: "4h 30m",
        fare: 480,
        seats: 38
    },
    {
        id: 5,
        number: "12124",
        name: "Deccan Express",
        from: "Mumbai",
        to: "Pune",
        departure: "07:00 AM",
        arrival: "10:25 AM",
        duration: "3h 25m",
        fare: 350,
        seats: 50
    },
    {
        id: 6,
        number: "12296",
        name: "Sanghamitra Express",
        from: "Bengaluru",
        to: "Chennai",
        departure: "09:00 PM",
        arrival: "05:00 AM",
        duration: "8h",
        fare: 600,
        seats: 27
    },
    {
        id: 7,
        number: "12302",
        name: "Kolkata Rajdhani",
        from: "Delhi",
        to: "Kolkata",
        departure: "05:00 PM",
        arrival: "10:00 AM",
        duration: "17h",
        fare: 1600,
        seats: 18
    }
];


// ========================================
// 2. GET HTML ELEMENTS
// ========================================

const searchForm = document.getElementById("searchForm");

const sourceInput = document.getElementById("source");

const destinationInput =
    document.getElementById("destination");

const journeyDateInput =
    document.getElementById("journeyDate");

const swapButton =
    document.getElementById("swapButton");

const resultsSection =
    document.getElementById("resultsSection");

const resultsSummary =
    document.getElementById("resultsSummary");

const resultCount =
    document.getElementById("resultCount");

const trainResults =
    document.getElementById("trainResults");

const bookingModal =
    document.getElementById("bookingModal");

const bookingForm =
    document.getElementById("bookingForm");

const selectedTrainInfo =
    document.getElementById("selectedTrainInfo");

const closeModal =
    document.getElementById("closeModal");

let selectedTrain = null;

let lastSearch = null;


// ========================================
// 3. SET THE DEFAULT JOURNEY DATE
// ========================================

function getLocalDate() {
    const today = new Date();

    const year = today.getFullYear();

    const month = String(
        today.getMonth() + 1
    ).padStart(2, "0");

    const day = String(
        today.getDate()
    ).padStart(2, "0");

    return `${year}-${month}-${day}`;
}

journeyDateInput.min = getLocalDate();

journeyDateInput.value = getLocalDate();


// ========================================
// 4. SWAP THE TWO STATIONS
// ========================================

swapButton.addEventListener("click", function () {

    const temporaryValue = sourceInput.value;

    sourceInput.value = destinationInput.value;

    destinationInput.value = temporaryValue;

});


// ========================================
// 5. SEARCH FOR TRAINS
// ========================================

searchForm.addEventListener("submit", function (event) {

    event.preventDefault();

    const source = sourceInput.value.trim();

    const destination = destinationInput.value.trim();

    const journeyDate = journeyDateInput.value;


    // Check that both stations are different.

    if (
        source.toLowerCase() ===
        destination.toLowerCase()
    ) {
        alert("Source and destination must be different.");
        return;
    }


    // Prevent past dates.

    if (journeyDate < getLocalDate()) {
        alert("Please select today or a future date.");
        return;
    }


    // Store the search details.

    lastSearch = {
        source: source,
        destination: destination,
        date: journeyDate
    };


    // Find trains matching the selected route.

    const matchingTrains = trains.filter(function (train) {

        return (
            train.from.toLowerCase() ===
                source.toLowerCase() &&

            train.to.toLowerCase() ===
                destination.toLowerCase()
        );

    });


    displayTrains(matchingTrains);

    resultsSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

});


// ========================================
// 6. DISPLAY TRAIN RESULTS
// ========================================

function displayTrains(matchingTrains) {

    resultsSection.hidden = false;

    trainResults.replaceChildren();

    resultsSummary.textContent =
        `${lastSearch.source} → ${lastSearch.destination} | ` +
        formatDate(lastSearch.date);

    resultCount.textContent =
        `${matchingTrains.length} train(s)`;


    // Display a message when no trains match.

    if (matchingTrains.length === 0) {

        const emptyState = document.createElement("div");

        emptyState.className = "empty-state";

        const heading = document.createElement("h3");

        heading.textContent = "No matching trains found";

        const message = document.createElement("p");

        message.textContent =
            "This demonstration contains only a few sample routes. " +
            "Try Delhi to Jaipur, Delhi to Mumbai, Jaipur to Delhi, " +
            "or Mumbai to Pune.";

        emptyState.append(heading, message);

        trainResults.appendChild(emptyState);

        return;
    }


    // Create a card for each matching train.

    matchingTrains.forEach(function (train) {

        const card = document.createElement("article");

        card.className = "train-card";


        // Train name and number.

        const trainInfo = document.createElement("div");

        const number = document.createElement("div");

        number.className = "train-number";

        number.textContent = `TRAIN ${train.number}`;

        const name = document.createElement("div");

        name.className = "train-name";

        name.textContent = train.name;

        const seats = document.createElement("div");

        seats.className = "train-duration";

        seats.textContent =
            `${train.seats} sample seats available`;

        trainInfo.append(number, name, seats);


        // Departure details.

        const departure = document.createElement("div");

        const departureTime = document.createElement("div");

        departureTime.className = "train-time";

        departureTime.textContent = train.departure;

        const departureStation = document.createElement("div");

        departureStation.className = "train-station";

        departureStation.textContent = train.from;

        const duration = document.createElement("div");

        duration.className = "train-duration";

        duration.textContent = train.duration;

        departure.append(
            departureTime,
            departureStation,
            duration
        );


        // Arrival details.

        const arrival = document.createElement("div");

        const arrivalTime = document.createElement("div");

        arrivalTime.className = "train-time";

        arrivalTime.textContent = train.arrival;

        const arrivalStation = document.createElement("div");

        arrivalStation.className = "train-station";

        arrivalStation.textContent = train.to;

        const arrivalLabel = document.createElement("div");

        arrivalLabel.className = "train-duration";

        arrivalLabel.textContent = "Arrival";

        arrival.append(
            arrivalTime,
            arrivalStation,
            arrivalLabel
        );


        // Fare and booking button.

        const booking = document.createElement("div");

        const fare = document.createElement("div");

        fare.className = "train-fare";

        fare.textContent =
            `₹${train.fare.toLocaleString("en-IN")}`;

        const fareLabel = document.createElement("div");

        fareLabel.className = "fare-label";

        fareLabel.textContent = "Sample fare";

        const bookButton = document.createElement("button");

        bookButton.type = "button";

        bookButton.className = "book-button";

        bookButton.dataset.trainId = String(train.id);

        bookButton.textContent = "Book Now →";

        booking.append(fare, fareLabel, bookButton);


        card.append(trainInfo, departure, arrival, booking);

        trainResults.appendChild(card);

    });

}


// ========================================
// 7. FORMAT THE JOURNEY DATE
// ========================================

function formatDate(dateString) {

    const date = new Date(dateString + "T00:00:00");

    return date.toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric"
    });

}


// ========================================
// 8. OPEN THE BOOKING FORM
// ========================================

trainResults.addEventListener("click", function (event) {

    const button = event.target.closest(".book-button");

    if (!button) {
        return;
    }

    const trainId = Number(button.dataset.trainId);

    selectedTrain = trains.find(function (train) {
        return train.id === trainId;
    });

    if (!selectedTrain || !lastSearch) {
        alert("Please search for a train first.");
        return;
    }

    selectedTrainInfo.textContent =
        `${selectedTrain.name} (${selectedTrain.number}) | ` +
        `${selectedTrain.from} → ${selectedTrain.to} | ` +
        `${formatDate(lastSearch.date)} | ` +
        `₹${selectedTrain.fare}`;

    bookingModal.hidden = false;

    document.getElementById("passengerName").focus();

});


// ========================================
// 9. CLOSE THE BOOKING FORM
// ========================================

closeModal.addEventListener("click", function () {

    bookingModal.hidden = true;

});


bookingModal.addEventListener("click", function (event) {

    if (event.target === bookingModal) {
        bookingModal.hidden = true;
    }

});


document.addEventListener("keydown", function (event) {

    if (event.key === "Escape") {
        bookingModal.hidden = true;
    }

});


// ========================================
// 10. DEMONSTRATION BOOKING
// ========================================

bookingForm.addEventListener("submit", function (event) {

    event.preventDefault();

    if (!selectedTrain || !lastSearch) {
        alert("Please select a train first.");
        return;
    }

    const passengerName =
        document.getElementById("passengerName")
            .value.trim();

    const passengerAge =
        Number(document.getElementById("passengerAge").value);

    const passengerPhone =
        document.getElementById("passengerPhone")
            .value.trim();


    // Validate the passenger details.

    if (!passengerName) {
        alert("Please enter the passenger's name.");
        return;
    }

    if (
        !Number.isInteger(passengerAge) ||
        passengerAge < 1 ||
        passengerAge > 120
    ) {
        alert("Please enter a valid age.");
        return;
    }

    if (!/^[0-9]{10}$/.test(passengerPhone)) {
        alert("Please enter a valid 10-digit phone number.");
        return;
    }


    // Generate a temporary demonstration ID.

    const demoId =
        "DEMO" + Date.now().toString().slice(-8);


    alert(
        "DEMO BOOKING CONFIRMATION\n\n" +
        "Booking ID: " + demoId + "\n" +
        "Passenger: " + passengerName + "\n" +
        "Train: " + selectedTrain.name + "\n" +
        "Train number: " + selectedTrain.number + "\n" +
        "Route: " +
        selectedTrain.from + " → " + selectedTrain.to + "\n" +
        "Journey date: " + formatDate(lastSearch.date) + "\n" +
        "Fare: ₹" + selectedTrain.fare + "\n\n" +
        "This is a demo. Nothing has been saved to MySQL."
    );


    bookingModal.hidden = true;

    bookingForm.reset();

    selectedTrain = null;

});