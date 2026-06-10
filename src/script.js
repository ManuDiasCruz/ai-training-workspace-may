const CARD_IMAGES = [
    "img/bobrossparrot.gif",
    "img/explodyparrot.gif",
    "img/fiestaparrot.gif",
    "img/metalparrot.gif",
    "img/revertitparrot.gif",
    "img/tripletsparrot.gif",
    "img/unicornparrot.gif",
];

const cardsElement = document.querySelector(".cards");
const movesElement = document.querySelector(".moves");
const timerElement = document.querySelector(".timer");
const pairsElement = document.querySelector(".pairs");
const settingsForm = document.querySelector(".game-settings");
const cardCountSelect = document.querySelector("#card-count");
const resultDialog = document.querySelector(".result-dialog");
const resultSummary = document.querySelector(".result-summary");
const playAgainButton = document.querySelector(".play-again");

let firstCard = null;
let secondCard = null;
let moves = 0;
let matchedPairs = 0;
let totalPairs = 0;
let elapsedSeconds = 0;
let timerId = null;
let flipBackId = null;
let boardLocked = false;

function shuffle(items) {
    const shuffledItems = [...items];

    for (let index = shuffledItems.length - 1; index > 0; index -= 1) {
        const randomIndex = Math.floor(Math.random() * (index + 1));
        [shuffledItems[index], shuffledItems[randomIndex]] = [
            shuffledItems[randomIndex],
            shuffledItems[index],
        ];
    }

    return shuffledItems;
}

function formatTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
    const seconds = (totalSeconds % 60).toString().padStart(2, "0");
    return `${minutes}:${seconds}`;
}

function updateStatus() {
    movesElement.textContent = moves;
    timerElement.textContent = formatTime(elapsedSeconds);
    pairsElement.textContent = `${matchedPairs} / ${totalPairs}`;
}

function startTimer() {
    if (timerId !== null) {
        return;
    }

    timerId = window.setInterval(() => {
        elapsedSeconds += 1;
        timerElement.textContent = formatTime(elapsedSeconds);
    }, 1000);
}

function stopTimer() {
    if (timerId !== null) {
        window.clearInterval(timerId);
        timerId = null;
    }
}

function createCard(imagePath, pairId, cardIndex) {
    const card = document.createElement("button");
    card.className = "card";
    card.type = "button";
    card.dataset.pairId = pairId;
    card.setAttribute("aria-label", `Hidden card ${cardIndex + 1}`);

    card.innerHTML = `
        <span class="card-face card-front" aria-hidden="true">
            <img src="img/front.png" alt="">
        </span>
        <span class="card-face card-back" aria-hidden="true">
            <img src="${imagePath}" alt="">
        </span>
    `;

    card.addEventListener("click", handleCardSelection);
    return card;
}

function buildDeck(cardCount) {
    const selectedImages = shuffle(CARD_IMAGES).slice(0, cardCount / 2);
    const pairedCards = selectedImages.flatMap((imagePath, pairId) => [
        { imagePath, pairId },
        { imagePath, pairId },
    ]);

    return shuffle(pairedCards);
}

function resetSelection() {
    firstCard = null;
    secondCard = null;
    boardLocked = false;
}

function finishGame() {
    stopTimer();
    resultSummary.textContent = `You matched ${totalPairs} pairs in ${moves} moves and ${formatTime(elapsedSeconds)}.`;

    window.setTimeout(() => {
        resultDialog.showModal();
    }, 450);
}

function checkSelectedPair() {
    const cardsMatch = firstCard.dataset.pairId === secondCard.dataset.pairId;

    if (cardsMatch) {
        firstCard.classList.add("is-matched");
        secondCard.classList.add("is-matched");
        firstCard.disabled = true;
        secondCard.disabled = true;
        firstCard.setAttribute("aria-label", "Matched parrot card");
        secondCard.setAttribute("aria-label", "Matched parrot card");
        matchedPairs += 1;
        updateStatus();
        resetSelection();

        if (matchedPairs === totalPairs) {
            finishGame();
        }

        return;
    }

    flipBackId = window.setTimeout(() => {
        firstCard.classList.remove("is-flipped");
        secondCard.classList.remove("is-flipped");
        firstCard.setAttribute("aria-label", "Hidden parrot card");
        secondCard.setAttribute("aria-label", "Hidden parrot card");
        flipBackId = null;
        resetSelection();
    }, 750);
}

function handleCardSelection(event) {
    const selectedCard = event.currentTarget;

    if (
        boardLocked
        || selectedCard === firstCard
        || selectedCard.classList.contains("is-matched")
        || selectedCard.classList.contains("is-flipped")
    ) {
        return;
    }

    startTimer();
    selectedCard.classList.add("is-flipped");
    selectedCard.setAttribute("aria-label", "Revealed parrot card");

    if (firstCard === null) {
        firstCard = selectedCard;
        return;
    }

    secondCard = selectedCard;
    moves += 1;
    boardLocked = true;
    updateStatus();
    checkSelectedPair();
}

function startNewGame(cardCount) {
    stopTimer();

    if (flipBackId !== null) {
        window.clearTimeout(flipBackId);
        flipBackId = null;
    }

    if (resultDialog.open) {
        resultDialog.close();
    }

    firstCard = null;
    secondCard = null;
    moves = 0;
    matchedPairs = 0;
    totalPairs = cardCount / 2;
    elapsedSeconds = 0;
    boardLocked = false;
    cardsElement.replaceChildren();

    const deck = buildDeck(cardCount);
    deck.forEach(({ imagePath, pairId }, cardIndex) => {
        cardsElement.append(createCard(imagePath, pairId, cardIndex));
    });

    updateStatus();
}

settingsForm.addEventListener("submit", (event) => {
    event.preventDefault();
    startNewGame(Number(cardCountSelect.value));
});

playAgainButton.addEventListener("click", () => {
    startNewGame(Number(cardCountSelect.value));
});

startNewGame(Number(cardCountSelect.value));
