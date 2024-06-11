import grpc
from concurrent import futures
import forca_pb2
import forca_pb2_grpc
import threading
import random

class GameState:
    def __init__(self):
        self.players = []
        self.scores = {}
        self.current_word = ""
        self.attempts_left = 6
        self.guessed_letters = set()
        self.current_player_index = 0
        self.game_over = False

    def reset(self):
        self.current_word = random.choice(["aquarela", "canguru", "framboesa", "gnomo", "kiwi", "metamorfose", "nectar", "ostra", "pipoca", "grpc", "trombone", "ritmo", "bussola", "labirinto", "oraculo", "samurai", "programacao", "tornado", "iguana", "guitarra"])
        self.attempts_left = 6
        self.guessed_letters = set()
        self.current_player_index = 0
        self.game_over = False

class ForcaServicer(forca_pb2_grpc.ForcaServicer):
    def __init__(self):
        self.game_state = GameState()
        self.lock = threading.Lock()
        self.clients = []

    def JoinGame(self, request, context):
        with self.lock:
            player_id = len(self.game_state.players) + 1
            player_name = request.player_name
            self.game_state.players.append(player_name)
            self.game_state.scores[player_name] = 0
            response = forca_pb2.JoinGameResponse(player_id=str(player_id), message=f"O/A jogador(a) {player_name} entrou no jogo.", players=self.game_state.players)
            if len(self.game_state.players) == 2:
                self.game_state.reset()
            return response

    def StartGame(self, request, context):
        print("servidor rodando na porta 50051, esperando jogadores..")
        return forca_pb2.StartGameResponse(message="O jogo começou!", success=True)

    def GuessLetter(self, request, context):
        with self.lock:
            if self.game_state.game_over:
                return forca_pb2.GuessLetterResponse(message="O jogo já acabou.", correct=False, game_over=True)

            player_name = self.game_state.players[int(request.player_id) - 1]
            if player_name != self.game_state.players[self.game_state.current_player_index]:
                return forca_pb2.GuessLetterResponse(message="Não é sua vez.", correct=False, game_over=False)

            letter = request.letter.lower()
            if letter in self.game_state.guessed_letters:
                return forca_pb2.GuessLetterResponse(message="Você já chutou essa letra.", correct=False, game_over=False)

            self.game_state.guessed_letters.add(letter)
            if letter in self.game_state.current_word:
                message = f"Correto! A letra '{letter}' está na palavra."
                correct = True
                if all(c in self.game_state.guessed_letters for c in self.game_state.current_word):
                    self.game_state.scores[player_name] += 1  # Incrementa a pontuação do jogador
                    message += f"\n---------------------------------------------\nFIM DE JOGO: {player_name} ganhou a rodada!\n---------------------------------------------"
                    self.game_state.reset()  # Reinicia o jogo após uma rodada
                else:
                    # Se acertou, continua na mesma rodada
                    return forca_pb2.GuessLetterResponse(
                        message=message,
                        correct=correct,
                        game_over=False,
                        points=self.game_state.scores[player_name]
                    )
            else:
                self.game_state.attempts_left -= 1
                message = f"Incorreto! A letra '{letter}' não está na palavra."
                correct = False
                if self.game_state.attempts_left == 0:
                    self.game_state.reset()  # Reinicia o jogo após uma rodada
                else:
                    # Passa a vez para o próximo jogador
                    self.game_state.current_player_index = (self.game_state.current_player_index + 1) % len(self.game_state.players)

            game_over = self.game_state.game_over

            return forca_pb2.GuessLetterResponse(
                message=message,
                correct=correct,
                game_over=game_over,
                points=self.game_state.scores[player_name]
            )

    def GetGameState(self, request, context):
        player_name = self.game_state.players[int(request.player_id) - 1]
        current_player = self.game_state.players[self.game_state.current_player_index]
        return forca_pb2.GetGameStateResponse(
            current_word=" ".join([c if c in self.game_state.guessed_letters else "_" for c in self.game_state.current_word]),
            attempts_left=self.game_state.attempts_left,
            guessed_letters=list(self.game_state.guessed_letters),
            current_player=current_player,
            scores=[forca_pb2.PlayerScore(player_name=name, score=score) for name, score in self.game_state.scores.items()],
            game_over=self.game_state.game_over,
            message="Estado do jogo atualizado."
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    forca_pb2_grpc.add_ForcaServicer_to_server(ForcaServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor rodando na porta 50051, esperando jogadores..")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
