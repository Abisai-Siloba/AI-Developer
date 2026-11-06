# Track A Day 5 Project: Python Tool for a Client
# A Python script that asks the user for a client name and a task, 
# then prints a formatted action summary. Example: Kamau Auto Spares, Task: Follow up on invoice #014. 
# Add a loop so the user can log multiple tasks before quitting. Save each entry to a text file called tasks.txt.
# Enter q at the client-name prompt to quit. Empty names or tasks aren’t saved.



from pathlib import Path

TASKS_FILE = Path(__file__).with_name("tasks.txt")

def main() -> None:
    print("Client Task Logger")
    print("Enter 'q' as the client name when you are finished.")

    while True:
        client_name = input("\nClient name: ").strip()
        if client_name.casefold() == "q":
            print("Goodbye!")
            break
        if not client_name:
            print("Client name cannot be empty.")
            continue

        task = input("Task: ").strip()
        if not task:
            print("Task cannot be empty. Please try again.")
            continue

        summary = f"{client_name}, Task: {task}"
        print(f"\n{summary}")

        with TASKS_FILE.open("a", encoding="utf-8") as tasks_file:
            tasks_file.write(f"{summary}\n")
        print("Saved to tasks.txt.")


if __name__ == "__main__":
    main()
