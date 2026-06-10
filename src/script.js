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

// Prende o usuário até digitar um número de cartas dentro das restrições do jogo
// (entre 4 e 14 cartas, sendo um número par)
let numCartas = parseInt(prompt("Com quantas cartas vocês quer jogar?"));

// Chamada a função iniciarJogo() para iniciar o jogo
iniciarJogo();

// Função usada para iniciar um novo jogo
function iniciarJogo(){
    validarQtdadecartas();
    geraCartasAleatorias();
    montarJogo();
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

    intervalo = null;
    timer = 0;

    let elemento = document.querySelector(".cartas");
    elemento.innerHTML ="";
    // // Outra maneira de limpar a div cuja class é .cartas é usando os seus filhos e chamando o parentNode
    // let elemento = document.querySelectorAll(".carta");

    // for(let i = 0; i < elemento.length; i++){
    //     elemento[i].parentNode.removeChild(elemento[i]);
    // }

}

// Função usada para validar a quantidade de cartas
// O jogo só funcionará com número de cartas pares entre, 4 e 14 inclusos
function validarQtdadecartas(){
    while ((numCartas<4)||(numCartas>14)||((numCartas%2)!=0)){
        numCartas = parseInt(prompt("Você deve digitar uma quantidade de cartas pares entre 4 e 14, inclusos!\nCom quantas cartas vocês quer jogar?"));
        print((numCartas<4)||(numCartas>14)||((numCartas%2)!=0));
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
    <div class="carta" data-identifier="card" onclick="selecionarCarta(this)">
        <div class="frente face" data-identifier="back-face">
            <img src="img/front.png" alt="">
        </div>
        <div class="verso face" data-identifier="front-face">
            <img src=${caminhoImg} alt="">
        </div>
    </div>
    `;
    return div;
    
}

// Função usada para virar a carta deixando o conteúdo da carta fora de vista
function desvirar(cartaClicada){
    cartaClicada.querySelector(".frente").classList.toggle("face-frente-virada");
    cartaClicada.querySelector(".verso").classList.toggle("face-verso-virada");
}

function atualizarQtdadeJogadas(){
    let elemento = document.querySelector(".qtdade-jogadas");
    elemento.innerHTML = qtdadeJogadas;
}

// Função usada para tratar o clique nas cartas
function selecionarCarta(cartaClicada) {
    if(clicouDuasCartas == false){
        if(primeiraCarta === null) {
            primeiraCarta = cartaClicada;
            qtdadeJogadas+=1;
            atualizarQtdadeJogadas();
            cartaClicada.querySelector(".frente").classList.toggle("face-frente-virada");
            cartaClicada.querySelector(".verso").classList.toggle("face-verso-virada");
        } else {
            cartaClicada.querySelector(".frente").classList.toggle("face-frente-virada");
            cartaClicada.querySelector(".verso").classList.toggle("face-verso-virada");
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
    if (primeiraCarta.isEqualNode(segundaCarta)){
        primeiraCarta = null;
        segundaCarta = null;
        qtdadeParesAbertos += 1;
        if(qtdadeParesAbertos == (numCartas/2)){
            alert("Você ganhou em " + qtdadeJogadas + " jogadas!");
            let novoJogo = prompt("Quer começar um novo jogo (sim/não)?");
            if (novoJogo == "sim"){
                limparVariaveis();
                numCartas = parseInt(prompt("Com quantas cartas vocês quer jogar?"));
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
const relogio = document.querySelector(".relogio");
let intervalo = null;
let timer = 0;

function aumentarContagem(){    
    relogio.innerHTML = " " + timer + " segundos";
    timer+=1;
}

intervalo = setInterval(aumentarContagem, 1000);
console.log(intervalo);