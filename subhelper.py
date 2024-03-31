def export_subtitiles(subs : list) -> None:
    """ Saves subtitles in the srt format

    Writes the subtitles in the output/subs.srt file
    
    Parameters
    ----------
    subs: list
        The subtitles to be saved

    """

    f = open("output/subs.srt", "w")
    index = 1
    for entry in subs:
        if entry[1] == "":
            continue
        f.write(str(index) + "\n")
        f.write("00:" + str(entry[0][0]) + ":00 -->" + "00:" + str(entry[0][1]) + ":00\n")
        f.write(entry[1] + "\n\n")
        index += 1
    f.close()