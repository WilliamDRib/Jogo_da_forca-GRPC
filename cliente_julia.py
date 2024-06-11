import grpc
import forca_pb2
import forca_pb2_grpc
import threading
import time

HANGMAN_PICS = [
    """
     -----
     |   |
         |
         |
         |
         |
    ========
    """,
    """
     -----
     |   |
     O   |
         |
         |
         |
    ========
    """,
    """
     -----
     |   |
     O   |
     |   |
         |
         |
    ========
    """,
    """
     -----
     |   |
     O   |
    /|   |
         |
         |
    ========
    """,
    """
     -----
     |   |
     O   |
    /|\  |
         |
         |
    ========
    """,
    """
     -----
     |   |
     O   |
    /|\  |
    /    |
         |
    ========
    """,
    """
     -----
     |   |
     O   |
    /|\  |
    / \  |
         |
    ========
    """
]

def get_game_state(stub, player_id):
    response = stub.GetGameState(forca_pb2.GetGameStateRequest(player_id=player_id))
    print(HANGMAN_PICS[6 - response.attempts_left])
    print(f"Palavra atual: {response.current_word}")
    print(f"Letras chutadas: {', '.join(response.guessed_letters)}")
    print(f"Tentativas restantes: {response.attempts_left}")
    print(f"Jogador atual: {response.current_player}")
    print("Pontuações:")
    for score in response.scores:
        print(f"{score.player_name}: {score.score}")
    return response

def run_client():
    channel = grpc.insecure_channel('localhost:50051')
    stub = forca_pb2_grpc.ForcaStub(channel)
    player_name = input("Digite seu nome: ")
    response = stub.JoinGame(forca_pb2.JoinGameRequest(player_name=player_name))
    player_id = response.player_id
    print(response.message)
    
    while True:
        game_state = get_game_state(stub, player_id)
        if len(game_state.scores) == 2:
            break
        else:
            print("Aguardando outro jogador...")
            time.sleep(2)

    start_response = stub.StartGame(forca_pb2.StartGameRequest(player_id=player_id))
    print(start_response.message)
    if start_response.success:
        game_state = get_game_state(stub, player_id)
        while not game_state.game_over:
            if game_state.current_player == player_name:
                letter = input("Chute uma letra: ")
                guess_response = stub.GuessLetter(forca_pb2.GuessLetterRequest(player_id=player_id, letter=letter))
                print(guess_response.message)
                if guess_response.correct:
                    game_state = get_game_state(stub, player_id)
                else:
                    game_state = get_game_state(stub, player_id)
            else:
                print(f"Vez do jogador {game_state.current_player}, aguarde...")
                game_state = get_game_state(stub, player_id)
                time.sleep(2)

if __name__ == '__main__':
    run_client()
