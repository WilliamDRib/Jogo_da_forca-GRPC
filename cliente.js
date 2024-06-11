const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const readline = require('readline');

const HANGMAN_PICS = [
  `
   -----
   |   |
       |
       |
       |
       |
  ========
  `,
  `
   -----
   |   |
   O   |
       |
       |
       |
  ========
  `,
  `
   -----
   |   |
   O   |
   |   |
       |
       |
  ========
  `,
  `
   -----
   |   |
   O   |
  /|   |
       |
       |
  ========
  `,
  `
   -----
   |   |
   O   |
  /|\  |
       |
       |
  ========
  `,
  `
   -----
   |   |
   O   |
  /|\  |
  /    |
       |
  ========
  `,
  `
   -----
   |   |
   O   |
  /|\  |
  / \  |
       |
  ========
  `
];

const packageDefinition = protoLoader.loadSync('./forca.proto', {
    keepCase: true, // Mantém os nomes dos campos como estão no .proto
    longs: String, // Converte tipos long para string
    enums: String, // Converte enums para string
    defaults: true, // Preenche campos ausentes com seus valores padrão
    oneofs: true // Adiciona suporte para campos oneof
});
const forcaProto = grpc.loadPackageDefinition(packageDefinition).forca;

function getGameState(stub, playerId) {
  return new Promise((resolve, reject) => {
    stub.GetGameState({ player_id: playerId }, (error, response) => {
      if (error) {
        reject(error);
      } else {
        console.log(HANGMAN_PICS[6 - response.attempts_left]);
        console.log(`
          Palavra atual: ${response.current_word}
          Tentativas restantes: ${response.attempts_left}
          Letras chutadas: ${response.guessed_letters.join(', ')}
          Jogador atual: ${response.current_player}
          Pontuações: ${response.scores.map(score => `${score.player_name}: ${score.score}`).join(', ')}
        `);
        resolve(response);
      }
    });
  });
}

async function runClient() {
  const client = new forcaProto.Forca('localhost:50051', grpc.credentials.createInsecure());

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const askQuestion = (question) => {
    return new Promise((resolve) => rl.question(question, resolve));
  };

  const playerName = await askQuestion('Digite seu nome: ');

  client.JoinGame({ player_name: playerName }, async (error, response) => {
    if (error) {
      console.error(error);
      rl.close();
      return;
    }
    
    const playerId = response.player_id;
    console.log(response.message);

    while (true) {
      const gameState = await getGameState(client, playerId);
      if (gameState.scores.length === 2) break;
      console.log('Aguardando outro jogador...');
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    client.StartGame({ player_id: playerId }, async (error, startResponse) => {
      if (error) {
        console.error(error);
        rl.close();
        return;
      }

      console.log(startResponse.message);

      if (startResponse.success) {
        let gameState = await getGameState(client, playerId);
        while (!gameState.game_over) {
          if (gameState.current_player === playerName) {
            const letter = await askQuestion('Chute uma letra: ');
            client.GuessLetter({ player_id: playerId, letter }, async (error, guessResponse) => {
              if (error) {
                console.error(error);
                rl.close();
                return;
              }

              console.log(guessResponse.message);
              gameState = await getGameState(client, playerId);
            });
          } else {
            console.log(`Vez do jogador ${gameState.current_player}, aguarde...`);
            await new Promise(resolve => setTimeout(resolve, 2000));
            gameState = await getGameState(client, playerId);
          }
        }
      }
      rl.close();
    });
  });
}

runClient();
