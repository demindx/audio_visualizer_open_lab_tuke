from client import AudioVisualizerClient

if __name__ == "__main__":
    client = AudioVisualizerClient("openlab.kpi.fei.tuke.sk", 1883)
    client.main_loop()
