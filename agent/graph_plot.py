from agent.graph import app

def main():
    print(app.get_graph().draw_mermaid())

if __name__ == "__main__":
    main()