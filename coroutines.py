


def time_delay(seconds):
    elapsed_time = 0
    print(f"Waiting for {seconds} seconds...")
    while elapsed_time < seconds:
        
        elapsed_time += 1  # Update elapsed time based on frame duration
        print(f"elapsed_time: {elapsed_time}")
        yield  # Simulate waiting for the next frame
    print(f"Time delay of {seconds} seconds finished!")

def trigger_abilities():
    yield print("1")
    yield from time_delay(2)
    yield print("3")




def turn_phases():
    yield print("1")
    yield from time_delay(2)
    yield print("3")

class Phase:
    is_done: bool = False

    def __init__(self) -> None:
        self.steps = turn_phases()

    def loop(self):
        try:
            next(self.steps)
        except StopIteration:
            #print("No more steps!")
            self.is_done = True

turn = Phase()

turn.loop()