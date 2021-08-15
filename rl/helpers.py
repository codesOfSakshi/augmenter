import nlpaug.augmenter.word as naw
import nlpaug.augmenter.char as nac
import nlpaug.augmenter.sentence as nas
import nlpaug.augmenter.audio as naa
import emoji
import random
import string

# helper functions are below

def evaluate_negative_augmentation(text, neg_logic, t, half_txt, rem_txt, n, words):

    if neg_logic == "OCR Augmentation":
        return nac.OcrAug().augment(text, n=1)
    elif neg_logic == "Antonym of text":
        return naw.AntonymAug().augment(text, n=1)
    elif neg_logic == "KeyBoard Augmentation":
        return nac.KeyboardAug().augment(text, n=1)
    elif neg_logic == "Random Char insert":
        return nac.RandomCharAug('insert').augment(text, n=1)
    elif neg_logic == "Random Char swap":
        return nac.RandomCharAug('swap').augment(text, n=1)
    elif neg_logic == "Random Char delete":
        return nac.RandomCharAug('delete').augment(text, n=1)
    elif neg_logic == "SpellingAug Augmentation":
        return naw.SpellingAug().augment(text, n=1)
    elif neg_logic == "SplitAug Augmentation":
        return naw.SplitAug().augment(text, n=1)


def get_with_special_char(text):
    """
    replace char in text
    """
    # get random indexes to be replaced with special characters which will be 35% of sentence but not more than 15 chars
    indexes = random.sample(range(0, len(text)), min(round(len(text) * 35 / 100), 15))
    for index in indexes:
        text = text[:index] + random.choice(string.punctuation) + text[index + 1:]

    return text


def text_to_emoji(text):
    """
    Replaces words with possible emojis.
    """
    text = text.replace(",", "").replace(".", "")
    new_sentence = " ".join([":" + s + ":" for s in text.split(" ")])
    emojized = emoji.emojize(new_sentence, use_aliases=True).split(" ")

    sent = []
    for each in emojized:
        if each in emoji.UNICODE_EMOJI['en']:
            sent.append(each)
        else:
            sent.append(each.replace(":", ""))
    return " ".join(sent)


def apply_pos_logic(logic, text, t):
    if logic == 'Text to Emoji':
        return text_to_emoji(text)
    elif logic == "Synonym Augmentation":
        return naw.SynonymAug(aug_src='wordnet').augment(text, n=1)
    elif logic == "ReservedAug Augmentation":
        return naw.ReservedAug(reserved_tokens=[]).augment(text, n=1)       


def apply_audio_pos_logic(wav, logic, sr):
    if logic == "LoudnessAug":
        return naa.LoudnessAug().augment(wav)
    elif logic == "PitchAug":
        return naa.PitchAug(sampling_rate=sr).augment(wav)
    elif logic == "NormalizeAug":
        return naa.NormalizeAug().augment(wav)
    elif logic == "SpeedAug":
        return naa.SpeedAug().augment(wav)
    elif logic == "VtlpAug":
        return naa.VtlpAug(sampling_rate=sr).augment(wav)
    elif logic == "PolarityInverseAug":
        return naa.PolarityInverseAug().augment(wav)


def apply_audio_neg_logic(wav, logic, sr):

    if logic == "CropAug":
        return naa.CropAug(sampling_rate=sr).augment(wav)
    elif logic == "MaskAug":
        return naa.MaskAug(mask_with_noise=False).augment(wav)
    elif logic == "ShiftAug":
        return naa.ShiftAug(sampling_rate=sr).augment(wav)
    elif logic == "NoiseAug":
        return naa.NoiseAug().augment(wav)

def get_next_counter(counter):

    int_part, dec_part = counter.split(".")
    dec_part = int(dec_part)+1
    size = len(str(dec_part))
    dec_part = dec_part/(10**size)
    counter =  format(int(int_part) + dec_part, f'.{size}f')
    return counter


