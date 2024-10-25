# This file run the simulation when executed

from .network import Network


def main():
    max_time = 3000

    network = Network()
    for _ in range(max_time):
        network.tick()

if __name__ == "__main__":
    main()
