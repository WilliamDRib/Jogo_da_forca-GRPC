import grpc
import forca_pb2
import forca_pb2_grpc
import os
import time

class ForcaClient:
    def __init__(self, channel):
        self.stub = forca_pb2_grpc.ForcaStub(channel)

    def join_game(self, player_name):
        response = self.stub.JoinGame(forca_pb2.JoinGameRequest(player_name=player_name))
        print(response.message)
        return response.player_id

    def start_game(self, player_id):
        response = self.stub.StartGame(forca_pb2.StartGameRequest(player_id=player_id))
        if response.success:
            print(response.message)
        else:
            print(response.message)

    def guess_letter(self, player_id, letter):
        response = self.stub.GuessLetter(forca_pb2.GuessLetterRequest(player_id=player_id, letter=letter))
        print(response.message)
        # self.draw_hangman(response.attempts_left)
        if response.correct:
            print("Correto!")
        else:
            print("Incorreto.")
        if response.game_over:
            print("Game over!")

    def get_game_state(self, player_id):
        response = self.stub.GetGameState(forca_pb2.GetGameStateRequest(player_id=player_id))
        self.clear_screen()
        print("Palavra atual:", response.current_word)
        print("Tentativas restantes :", response.attempts_left)
        print("Letras:", ', '.join(response.guessed_letters))
        print("Jogador atual:", response.current_player)
        print("Potuação:")
        for player_score in response.scores:
            print(f"{player_score.player_name}: {player_score.score}")
        self.draw_hangman(response.attempts_left)
        if response.game_over:
            print("Game over!")
        print(response.message)
        return response

    def draw_hangman(self, attempts_left):
        stages = [
            """
               -----
               |   |
               O   |
              /|\\  |
              / \\  |
                   |
            =========
            """,
            """
               -----
               |   |
               O   |
              /|\\  |
              /    |
                   |
            =========
            """,
            """
               -----
               |   |
               O   |
              /|\\  |
                   |
                   |
            =========
            """,
            """
               -----
               |   |
               O   |
              /|   |
                   |
                   |
            =========
            """,
            """
               -----
               |   |
               O   |
               |   |
                   |
                   |
            =========
            """,
            """
               -----
               |   |
               O   |
                   |
                   |
                   |
            =========
            """,
            """
               -----
               |   |
                   |
                   |
                   |
                   |
            =========
            """
        ]
        print(stages[attempts_left])

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

def run():
    # Conectando ao servidor gRPC
    with grpc.insecure_channel('localhost:50051') as channel:
        client = ForcaClient(channel)

        # Entrando no jogo
        player_name = input("Digite seu nome: ")
        player_id = client.join_game(player_name)

        # Iniciando o jogo
        input("Pressione Enter para iniciar o jogo...")
        client.start_game(player_id)

        # Loop principal do jogo
        while True:
            game_state = client.get_game_state(player_id)
            if game_state.current_player == player_name:
                letter = input("Digite a letra: ").lower()
                client.guess_letter(player_id, letter)
            time.sleep(3)  # Aguarda um pouco antes de atualizar novamente

if __name__ == '__main__':
    run()
