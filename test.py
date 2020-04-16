
def test(setPosition):
    hiPosition = int(setPosition / 65536)
    lowPosition = setPosition % 65536
    print(f"set: {setPosition} hiPos: {hiPosition}, lowPos: {lowPosition} check: {setPosition} = {hiPosition * 65536 + lowPosition}")
    return

test(3500)
