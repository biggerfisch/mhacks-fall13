from itertools import cycle, islice

def sum_n(series, n):
    return sum(islice(series,0,n))

def scale(intervals):
    def this_scale(degree):
        deg = degree - 1
        if not deg < 0:
            return sum_n(cycle(intervals), deg)
        else:
            deg2 = -deg + 1
            return - (scale(list(reversed(intervals))))(deg2)
    return this_scale

major = scale([2,2,1,2,2,2,1])

def shift_mode(mode, steps):
    def shifted(deg):
        return mode(steps + deg) - mode(steps + 1)
    return shifted

locrian    = shift_mode(major -1)
aeolian    = shift_mode(major -2)
mixolydian = shift_mode(major -3)
lydian     = shift_mode(major -4)
phrygian   = shift_mode(major -5)
dorian     = shift_mode(major -6)

def chord(mode, root, intervals):
    return [root - 1 + mode(i) for i in intervals]

def triad(mode,root):
    return chord(mode,root,[1,3,5])

def invert_6(mode,root):
    return chord(mode,root,[3,5,8])

def invert_6_4(mode,root):
    return chord(mode,root,[5,8,10])

def with_7(mode,root):
    return chord(mode,root,[1,3,5,7])

def slash_chord(left, right):
    c = voice_chord(left)
    return [x + major(int(right)) for x in c]

def voice_chord(url):
    if url[0] == 'b':
        mode = aeolian
    elif url[0] == 'M':
        mode = mixolydian
    elif url[0] == 'L':
        mode = lydian
    elif url[0] == 'C':
        mode = locrian
    elif url[0] == 'Y':
        mode = phrygian
    elif url[0] == 'D':
        mode = dorian
    else:
        mode = major
    
    slash_match = re.compile(r'(.*)/(\d)$').match(url)
    if slash_match:
        return slash_chord(slash_match.group(1), slash_match.group(2))
    
    chords = [(r'(\d)$', triad),
            (r'(\d)6$', invert_6),
            (r'(\d)64$', invert_6_4),
            (r'(\d)7$', with_7)]
    for r, f in chords:
        match = re.compile(r).search(url)
        if match:
            return f(mode, int(match.group(1)))
