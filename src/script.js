// Criação das cartas como objeto
const carta0 = {nome: "img/bobrossparrot.gif", id: 0}
const carta1 = {nome: "img/explodyparrot.gif", id: 1}
const carta2 = {nome: "img/fiestaparrot.gif", id: 2}
const carta3 = {nome: "img/metalparrot.gif", id: 3}
const carta4 = {nome: "img/revertitparrot.gif", id: 4}
const carta5 = {nome: "img/tripletsparrot.gif", id: 5}
const carta6 = {nome: "img/unicornparrot.gif", id: 6}

// Criação de um array com todos os objetos cartas
const cartas = []
cartas.push(carta0);
cartas.push(carta1);
cartas.push(carta2);
cartas.push(carta3);
cartas.push(carta4);
cartas.push(carta5);
cartas.push(carta6);

// Vetor para guardar as cartas que estão em jogo
let cartasEmJogo = [];

// variáveis globais usadas para auxilixar o controle do jogo
let primeiraCarta = null;
let segundaCarta = null;

let qtdadeJogadas = 0;
let qtdadeParesAbertos = 0;
let clicouDuasCartas = false;

let contador = 0;
const relogio = document.querySelector(".relogio");
let intervalo = null;
let timer = 0;

// Prende o usuário até digitar um número de cartas dentro das restrições do jogo
// (entre 4 e 14 cartas, sendo um número par)
let numCartas = obterQtdadeCartasInicial();

// Chamada a função iniciarJogo() para iniciar o jogo
iniciarJogo();

// Função usada para iniciar um novo jogo
function iniciarJogo(){
    validarQtdadecartas();
    geraCartasAleatorias();
    montarJogo();
    atualizarQtdadeJogadas();
    iniciarRelogio();
}

// Função usada para limpar as variáveis globais
function limparVariaveis(){
    cartasEmJogo = [];
    primeiraCarta = null;
    segundaCarta = null;

    qtdadeJogadas = 0;
    qtdadeParesAbertos = 0;
    clicouDuasCartas = false;

    contador = 0;

    clearInterval(intervalo);
    intervalo = null;
    timer = 0;
    atualizarRelogio();

    let elemento = document.querySelector(".cartas");
    elemento.innerHTML ="";
    document.querySelector(".fim-jogo").innerHTML = "";
    // // Outra maneira de limpar a div cuja class é .cartas é usando os seus filhos e chamando o parentNode
    // let elemento = document.querySelectorAll(".carta");

    // for(let i = 0; i < elemento.length; i++){
    //     elemento[i].parentNode.removeChild(elemento[i]);
    // }

}

function qtdadeCartasValida(qtdadeCartas) {
    return Number.isInteger(qtdadeCartas) && qtdadeCartas >= 4 && qtdadeCartas <= 14 && qtdadeCartas % 2 === 0;
}

function obterQtdadeCartasInicial() {
    const params = new URLSearchParams(window.location.search);
    const qtdadeCartasUrl = parseInt(params.get("cards"), 10);

    if (qtdadeCartasValida(qtdadeCartasUrl)) {
        return qtdadeCartasUrl;
    }

    return parseInt(prompt("Com quantas cartas você quer jogar?"), 10);
}

// Função usada para validar a quantidade de cartas
// O jogo só funcionará com número de cartas pares entre, 4 e 14 inclusos
function validarQtdadecartas(){
    while (!qtdadeCartasValida(numCartas)){
        numCartas = parseInt(prompt("Você deve digitar uma quantidade de cartas par entre 4 e 14.\nCom quantas cartas você quer jogar?"), 10);
    }
}

// Função usada para gerar um array contendo pares das cartas do jogo 
// aleatoriamente em um array :cartasEmJogo:
function geraCartasAleatorias(){
    // Algoritmo de embaralhamento de Fisher-Yates
    let list = [];
    for(let i=0; i<(numCartas/2); i++){
        list.push(i);
    }

    let randomNumber;
    let tmp;
    for (let i = list.length; i;) {
        randomNumber = Math.random() * i-- | 0;
        tmp = list[randomNumber];
        // troca o número aleatório pelo atual
        list[randomNumber] = list[i];
        // troca o atual pelo aleatório
        list[i] = tmp;
        cartasEmJogo.push(cartas[list[i]]);
    } 

    for (let i = list.length; i;) {
        randomNumber = Math.random() * i-- | 0;
        tmp = list[randomNumber];
        // troca o número aleatório pelo atual
        list[randomNumber] = list[i];
        // troca o atual pelo aleatório
        list[i] = tmp;
        cartasEmJogo.push(cartas[list[i]]);
    } 
}

// Função para criar a div que será renderizada na tela com as imagesn da carta 
function renderizarCarta(caminhoImg){
    const div = `
    <button class="carta" type="button" data-card="${caminhoImg}" data-identifier="card" onclick="selecionarCarta(this)" aria-label="Carta virada para baixo">
        <div class="frente face" data-identifier="back-face">
            <img src="img/front.png" alt="Verso da carta">
        </div>
        <div class="verso face" data-identifier="front-face">
            <img src="${caminhoImg}" alt="Papagaio da carta">
        </div>
    </button>
    `;
    return div;
    
}

// Função usada para virar a carta deixando o conteúdo da carta fora de vista
function desvirar(cartaClicada){
    cartaClicada.classList.remove("carta-virada");
    cartaClicada.setAttribute("aria-label", "Carta virada para baixo");
}

function virar(cartaClicada){
    cartaClicada.classList.add("carta-virada");
    cartaClicada.setAttribute("aria-label", "Carta virada para cima");
}

function atualizarQtdadeJogadas(){
    let elemento = document.querySelector(".qtdade-jogadas");
    elemento.innerHTML = qtdadeJogadas;
}

// Função usada para tratar o clique nas cartas
function selecionarCarta(cartaClicada) {
    if(clicouDuasCartas == false && cartaClicada !== primeiraCarta && !cartaClicada.classList.contains("carta-resolvida")){
        if(primeiraCarta === null) {
            primeiraCarta = cartaClicada;
            qtdadeJogadas+=1;
            atualizarQtdadeJogadas();
            virar(cartaClicada);
        } else {
            virar(cartaClicada);
            segundaCarta = cartaClicada;
            qtdadeJogadas+=1;
            atualizarQtdadeJogadas();
            clicouDuasCartas = true;

            setTimeout(validarPar, 1000);
        }
    }
}

// Função usada para validar se o par de cartas selecionadas são iguais ou não
// bem como para encerra o jogo
function validarPar(){
    if (primeiraCarta.dataset.card === segundaCarta.dataset.card){
        primeiraCarta.classList.add("carta-resolvida");
        segundaCarta.classList.add("carta-resolvida");
        primeiraCarta.setAttribute("aria-label", "Par encontrado");
        segundaCarta.setAttribute("aria-label", "Par encontrado");
        primeiraCarta = null;
        segundaCarta = null;
        qtdadeParesAbertos += 1;
        if(qtdadeParesAbertos == (numCartas/2)){
            alert("Você ganhou em " + qtdadeJogadas + " jogadas!");
            let novoJogo = prompt("Quer começar um novo jogo (sim/não)?");
            if (novoJogo == "sim"){
                limparVariaveis();
                numCartas = parseInt(prompt("Com quantas cartas você quer jogar?"), 10);
                iniciarJogo();
            }else{
                limparVariaveis();
                qtdadeJogadas = 0;
                atualizarQtdadeJogadas();
                let elemento = document.querySelector(".fim-jogo");
                elemento.innerHTML = "FIM DE JOGO!";
            }
        }

    }else{
        desvirar(primeiraCarta);    
        desvirar(segundaCarta);
        primeiraCarta = null;
        segundaCarta = null;
    }
    clicouDuasCartas = false;
}

// Função para montar as cartas do jogo na tela
function montarJogo(){
    let elemento = document.querySelector(".cartas");
    for (let i=0; i<numCartas; i++){
        const carta = cartasEmJogo[i];
        const aux = renderizarCarta(carta.nome);
        elemento.innerHTML += aux;
    }
}


// Variáveis e função para fazer contegem do tempo de jogo
function atualizarRelogio() {
    relogio.innerHTML = " " + timer + " segundos";
}

function aumentarContagem(){    
    timer+=1;
    atualizarRelogio();
}

function iniciarRelogio() {
    clearInterval(intervalo);
    timer = 0;
    atualizarRelogio();
    intervalo = setInterval(aumentarContagem, 1000);
}
