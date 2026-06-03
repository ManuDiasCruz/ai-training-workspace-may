const cartas = [
    { nome: "img/bobrossparrot.gif", id: "bobrossparrot" },
    { nome: "img/explodyparrot.gif", id: "explodyparrot" },
    { nome: "img/fiestaparrot.gif", id: "fiestaparrot" },
    { nome: "img/metalparrot.gif", id: "metalparrot" },
    { nome: "img/revertitparrot.gif", id: "revertitparrot" },
    { nome: "img/tripletsparrot.gif", id: "tripletsparrot" },
    { nome: "img/unicornparrot.gif", id: "unicornparrot" }
];

let cartasEmJogo = [];
let primeiraCarta = null;
let segundaCarta = null;
let qtdadeJogadas = 0;
let qtdadeParesAbertos = 0;
let clicouDuasCartas = false;
let intervalo = null;
let timer = 0;

const relogio = document.querySelector(".relogio");

function solicitarQtdadeCartas(mensagem) {
    return Number.parseInt(prompt(mensagem), 10);
}

let numCartas = solicitarQtdadeCartas("Com quantas cartas voce quer jogar?");

function qtdadeCartasValida(valor) {
    return Number.isInteger(valor) && valor >= 4 && valor <= 14 && valor % 2 === 0;
}

function validarQtdadecartas() {
    while (!qtdadeCartasValida(numCartas)) {
        numCartas = solicitarQtdadeCartas("Digite um numero par entre 4 e 14, inclusive.\nCom quantas cartas voce quer jogar?");
    }
}

function embaralhar(lista) {
    for (let i = lista.length; i > 0;) {
        const indiceAleatorio = Math.floor(Math.random() * i);
        i -= 1;
        const cartaAtual = lista[i];
        lista[i] = lista[indiceAleatorio];
        lista[indiceAleatorio] = cartaAtual;
    }

    return lista;
}

function geraCartasAleatorias() {
    const cartasEscolhidas = cartas.slice(0, numCartas / 2);
    cartasEmJogo = embaralhar([...cartasEscolhidas, ...cartasEscolhidas]);
}

function renderizarCarta(caminhoImg, idParrot) {
    return `
        <div class="carta" data-identifier="card" data-parrot="${idParrot}" onclick="selecionarCarta(this)">
            <div class="frente face" data-identifier="back-face">
                <img src="img/front.png" alt="frente da carta">
            </div>
            <div class="verso face" data-identifier="front-face">
                <img src="${caminhoImg}" alt="${idParrot}">
            </div>
        </div>
    `;
}

function montarJogo() {
    const elemento = document.querySelector(".cartas");
    elemento.innerHTML = cartasEmJogo
        .map((carta) => renderizarCarta(carta.nome, carta.id))
        .join("");
}

function virarCarta(cartaClicada) {
    cartaClicada.querySelector(".frente").classList.add("face-frente-virada");
    cartaClicada.querySelector(".verso").classList.add("face-verso-virada");
}

function desvirarCarta(cartaClicada) {
    cartaClicada.querySelector(".frente").classList.remove("face-frente-virada");
    cartaClicada.querySelector(".verso").classList.remove("face-verso-virada");
}

function atualizarQtdadeJogadas() {
    document.querySelector(".qtdade-jogadas").innerHTML = qtdadeJogadas;
}

function aumentarContagem() {
    relogio.innerHTML = " " + timer + " segundos";
    timer += 1;
}

function reiniciarRelogio() {
    if (intervalo !== null) {
        clearInterval(intervalo);
    }

    timer = 0;
    aumentarContagem();
    intervalo = setInterval(aumentarContagem, 1000);
}

function limparVariaveis() {
    cartasEmJogo = [];
    primeiraCarta = null;
    segundaCarta = null;
    qtdadeJogadas = 0;
    qtdadeParesAbertos = 0;
    clicouDuasCartas = false;

    if (intervalo !== null) {
        clearInterval(intervalo);
        intervalo = null;
    }

    timer = 0;
    relogio.innerHTML = " 0 segundos";
    document.querySelector(".cartas").innerHTML = "";
    document.querySelector(".fim-jogo").innerHTML = "";
}

function finalizarJogo() {
    clearInterval(intervalo);
    intervalo = null;

    alert("Voce ganhou em " + qtdadeJogadas + " jogadas!");
    const novoJogo = prompt("Quer comecar um novo jogo (sim/nao)?");

    if (novoJogo === "sim") {
        limparVariaveis();
        numCartas = solicitarQtdadeCartas("Com quantas cartas voce quer jogar?");
        iniciarJogo();
        return;
    }

    document.querySelector(".fim-jogo").innerHTML = "FIM DE JOGO!";
}

function validarPar() {
    const parValido = primeiraCarta.dataset.parrot === segundaCarta.dataset.parrot;

    if (parValido) {
        primeiraCarta.classList.add("encontrada");
        segundaCarta.classList.add("encontrada");
        qtdadeParesAbertos += 1;

        if (qtdadeParesAbertos === numCartas / 2) {
            finalizarJogo();
        }
    } else {
        desvirarCarta(primeiraCarta);
        desvirarCarta(segundaCarta);
    }

    primeiraCarta = null;
    segundaCarta = null;
    clicouDuasCartas = false;
}

function selecionarCarta(cartaClicada) {
    if (
        clicouDuasCartas ||
        cartaClicada.classList.contains("encontrada") ||
        cartaClicada === primeiraCarta
    ) {
        return;
    }

    virarCarta(cartaClicada);
    qtdadeJogadas += 1;
    atualizarQtdadeJogadas();

    if (primeiraCarta === null) {
        primeiraCarta = cartaClicada;
        return;
    }

    segundaCarta = cartaClicada;
    clicouDuasCartas = true;
    setTimeout(validarPar, 1000);
}

function iniciarJogo() {
    validarQtdadecartas();
    geraCartasAleatorias();
    montarJogo();
    atualizarQtdadeJogadas();
    reiniciarRelogio();
}

iniciarJogo();
