from tomtom import TomTomFormulator

Items = dict()
for formulator in [TomTomFormulator]:
    Items[formulator.DISPLAY_NAME] = formulator
