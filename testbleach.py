import bleach

def comparestrings(string_a, string_b):
    li = []
    string_a = set(string_a)

    for char in string_a:
        if char not in string_b:
            li.append(char)
    if len(li) > 0:
        print(f'Your username should not contain & and # as well as these characters: {", ".join(i for i in li)}')

string_a = 'Syhy9K3fMlAk/UvetfIYheXqKFZLhp4xUz9ZRi8LMAOFxCWRwTZeCyR1QdvWi502z3T6JHjYSuUgjKMIP7cw1ZpTppgwhRrko1QUTJ8Oi2PosK9LSA15hX4KMzDdSKSSMSTGCOmHoiHix8vCrneISUaOwtHpZAIxMAsEkZlHWkkPTxBPaEcq5aho3yw547EyLfMlrmm19SZIwUChgOGuRU2HEnbMeeGi8gwbDVVwhpq49KpBjhBMyiD2QF5BW0su3Huw/IfpW394rh9u+IEjpyP+e7aAeW43qYDnRKVkeboYTT34KHKs7XXSidvYoMNRHTbSRYYeQpZDkchIiNKUsw=='
string_b = bleach.clean(string_a)
print(f'string_b: {string_b}')

comparestrings(string_a, string_b)
