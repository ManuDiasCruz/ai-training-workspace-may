const cards = [
    { name: "img/bobrossparrot.gif", id: "bobross" },
    { name: "img/explodyparrot.gif", id: "explody" },
    { name: "img/fiestaparrot.gif", id: "fiesta" },
    { name: "img/metalparrot.gif", id: "metal" },
    { name: "img/revertitparrot.gif", id: "revertit" },
    { name: "img/tripletsparrot.gif", id: "triplets" },
    { name: "img/unicornparrot.gif", id: "unicorn" },
];

const board = document.querySelector(".cartas");
const movesElement = document.querySelector(".qtdade-jogadas");
const timerElement = document.querySelector(".relogio");
const resultElement = document.querySelector(".fim-jogo");
const startButton = document.querySelector(".start-button");
const cardOptionButtons = document.querySelectorAll(".card-option");

let selectedCardCount = 8;
let firstCard = null;
let secondCard = null;
let matchedPairs = 0;
let moves = 0;
let seconds = 0;
let timerId = null;
let boardLocked = false;

cardOptionButtons.forEach((button) => {
    button.addEventListener("click", () => {
        selectedCardCount = Number(button.dataset.cardCount);
        updateSelectedCardOption();
    });
});

startButton.addEventListener("click", () => {
    startGame(selectedCardCount);
});

updateSelectedCardOption();
startGame(selectedCardCount);

function startGame(cardCount) {
    resetGameState();
    renderCards(createDeck(cardCount));
    startTimer();
    startButton.textContent = "New game";
}

function resetGameState() {
    window.clearInterval(timerId);
    firstCard = null;
    secondCard = null;
    matchedPairs = 0;
    moves = 0;
    seconds = 0;
    boardLocked = false;
    board.innerHTML = "";
    resultElement.textContent = "";
    updateMoves();
    updateTimer();
}

function createDeck(cardCount) {
    const selectedCards = shuffle([...cards]).slice(0, cardCount / 2);
    const pairedCards = [...selectedCards, ...selectedCards].map((card, index) => ({
        ...card,
        instanceId: `${card.id}-${index}`,
    }));

    return shuffle(pairedCards);
}

function renderCards(deck) {
    const cardsMarkup = deck.map((card) => renderCard(card)).join("");
    board.innerHTML = cardsMarkup;

    board.querySelectorAll(".carta").forEach((cardElement) => {
        cardElement.addEventListener("click", () => selectCard(cardElement));
    });
}

function renderCard(card) {
    return `
        <button class="carta" type="button" data-card-id="${card.id}" data-instance-id="${card.instanceId}" data-identifier="card" aria-label="Hidden parrot card">
            <span class="frente face" data-identifier="back-face">
                <img src="img/front.png" alt="">
            </span>
            <span class="verso face" data-identifier="front-face">
                <img src="${card.name}" alt="">
            </span>
        </button>
    `;
}

function selectCard(cardElement) {
    if (
        boardLocked ||
        cardElement === firstCard ||
        cardElement.classList.contains("is-matched")
    ) {
        return;
    }

    flipCard(cardElement);
    moves += 1;
    updateMoves();

    if (firstCard === null) {
        firstCard = cardElement;
        return;
    }

    secondCard = cardElement;
    boardLocked = true;
    window.setTimeout(resolveSelectedCards, 700);
}

function resolveSelectedCards() {
    if (firstCard.dataset.cardId === secondCard.dataset.cardId) {
        markMatched(firstCard);
        markMatched(secondCard);
        matchedPairs += 1;

        if (matchedPairs === selectedCardCount / 2) {
            finishGame();
        }
    } else {
        hideCard(firstCard);
        hideCard(secondCard);
    }

    firstCard = null;
    secondCard = null;
    boardLocked = false;
}

function flipCard(cardElement) {
    cardElement.classList.add("is-flipped");
    cardElement.setAttribute("aria-label", "Revealed parrot card");
}

function hideCard(cardElement) {
    cardElement.classList.remove("is-flipped");
    cardElement.setAttribute("aria-label", "Hidden parrot card");
}

function markMatched(cardElement) {
    cardElement.classList.add("is-matched");
    cardElement.disabled = true;
    cardElement.setAttribute("aria-label", "Matched parrot card");
}

function finishGame() {
    window.clearInterval(timerId);
    resultElement.textContent = `You won in ${moves} moves and ${seconds}s.`;
}

function updateMoves() {
    movesElement.textContent = moves;
}

function startTimer() {
    timerId = window.setInterval(() => {
        seconds += 1;
        updateTimer();
    }, 1000);
}

function updateTimer() {
    timerElement.textContent = `${seconds}s`;
}

function updateSelectedCardOption() {
    cardOptionButtons.forEach((button) => {
        const isSelected = Number(button.dataset.cardCount) === selectedCardCount;
        button.classList.toggle("is-selected", isSelected);
        button.setAttribute("aria-pressed", String(isSelected));
    });
}

function shuffle(list) {
    const shuffled = [...list];

    for (let index = shuffled.length - 1; index > 0; index -= 1) {
        const randomIndex = Math.floor(Math.random() * (index + 1));
        const current = shuffled[index];
        shuffled[index] = shuffled[randomIndex];
        shuffled[randomIndex] = current;
    }

    return shuffled;
}
