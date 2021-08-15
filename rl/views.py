# -- coding: utf-8 --
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
import nlpaug
import random
import string
import soundfile as sf
import nlpaug.augmenter.word as naw
import nlpaug.augmenter.char as nac
import nlpaug.augmenter.sentence as nas
import nlpaug.augmenter.audio as naa
import nltk
import librosa
from textaugment import EDA, Wordnet
import emoji
from .models import Parent, Positive, Negative
import decimal
import math
from django.conf import settings as django_settings
import os
from .automold import *
from .automold_helper import *
from .helpers import *


positive_options = [
    "Text to emoji",
    "Synonym Augmentation",
    "ReservedAug Augmentation",
]
negative_options = [
    "OCR Augmentation",
    "Antonym of text",
    "KeyBoard Augmentation",
    "Random Char insert",
    "Random Char swap",
    "Random Char delete",
    "SpellingAug Augmentation",
    "SplitAug Augmentation",
]


@transaction.atomic
def audio_form(request):
    positive_options = [
        "LoudnessAug",
        "PitchAug",
        "NormalizeAug",
        "SpeedAug",
        "VtlpAug",
        "PolarityInverseAug",
    ]

    negative_options = [
        "CropAug",
        "MaskAug",        
        "NoiseAug",
        "ShiftAug",
    ]

    if request.method == 'POST':
        pos_logics = request.POST.getlist('pos-logic')
        neg_logics = request.POST.getlist('neg-logic')

        upload_file = request.FILES['voice']
        wav, sr = librosa.load(upload_file)
        for logic in pos_logics:
            wav = apply_audio_pos_logic(wav, logic, sr) 
        
        for logic in neg_logics:
            wav = apply_audio_neg_logic(wav, logic, sr)

        if (pos_logics or neg_logics) and wav is not None:
            sf.write(os.path.join(django_settings.STATIC_ROOT,'augment_audio.wav'), wav, sr)
        
        return render(request, 'audio.html', { "input_text":"", "result":wav, "positive_options": positive_options, "negative_options": negative_options})

    return render(request, 'audio.html', { "input_text":"", "result":None, "positive_options": positive_options, "negative_options": negative_options})


@transaction.atomic
def text_form(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        input_id = int(request.POST.get('input_id'))
        result = []
        pos_logics = request.POST.getlist('pos-logic')
        neg_logics = request.POST.getlist('neg-logic')

        # parent for the input text
        parent = Parent.objects.filter(sentence=text).last()
        if parent and parent.input_id!=input_id:
            messages.error(request,f'Invalid input id! Sentence exists with input id {parent.input_id}')
            return redirect('/index')
        elif not parent:
            parent = Parent.objects.create(sentence=text, input_id=input_id)

        source_text = text

        if pos_logics:
            t = None

            logics = []

            for logic in pos_logics:
                text = apply_pos_logic(logic, text, t) 
                logics.append(logic)

            if logics:
                last_positive = Positive.objects.filter(parent_id=parent.input_id).last()
                if not last_positive:
                    counter = int(parent.input_id) + 0.1
                    counter = f"P-{counter}"
                else:
                    current_counter = last_positive.positive_id.split("-")[1]
                    counter = get_next_counter(current_counter)
                    counter = f"P-{counter}"


                Positive.objects.create(sentence=text, parent_id=parent.input_id, positive_id=counter)
                parent.last_positive_id = counter
                parent.save()
                result.append([counter, text])


        elif neg_logics:
            t = None
            words = text.split(" ")
            half_txt = " ".join(words[:int(len(words) / 2)])
            rem_txt = " ".join(words[int(len(words) / 2):])
            n = int(len(words) / 2)

            logics = []
            for logic in neg_logics:
                if text:
                    text = evaluate_negative_augmentation(text, logic, t, half_txt, rem_txt, n, words)
                    if text:
                        words = text.split(" ")
                        if words:
                            half_txt = " ".join(words[:int(len(words) / 2)])
                            rem_txt = " ".join(words[int(len(words) / 2):])
                            n = int(len(words) / 2)
                            logics.append(logic)
                else:
                    text = source_text

            if logics:
                last_negative = Negative.objects.filter(parent_id=parent.input_id).last()
                if not last_negative:
                    counter = int(parent.input_id) + 0.1
                    counter = f"N-{counter}"
                else:
                    current_counter = last_negative.negative_id.split("-")[1]
                    counter = get_next_counter(current_counter)
                    counter = f"N-{counter}"

                Negative.objects.create(sentence=text, parent_id=parent.input_id, negative_id=counter)
                parent.last_negative_id = counter
                parent.save()
                result.append([counter, text])

        return render(request, 'index.html', {"input_text":source_text, "result":result, "positive_options": positive_options, "negative_options": negative_options})
    return render(request, 'index.html', {"input_text":"", "result":[], "positive_options": positive_options, "negative_options": negative_options})



@transaction.atomic
def image_form(request):

    if request.method == 'POST':

        upload_file = request.FILES['image']
        fs = FileSystemStorage()
        try:
            os.remove(os.path.join(django_settings.MEDIA_ROOT, "aug_image.jpeg"))
        except:
            pass

        filename = fs.save("aug_image.jpeg", upload_file)
        uploaded_file_path = fs.path(filename)
        images = load_images(uploaded_file_path)

        # brighten
        #bright_images= brighten(images[0])
        bright_images = darken(images[0])
        write_images(os.path.join(django_settings.STATIC_ROOT,'augment_image.jpeg'), bright_images) 
        
        return render(request, 'image.html', { "result":bright_images[0], "positive_options": positive_options, "negative_options": negative_options})

    return render(request, 'image.html', { "result":None, "positive_options": positive_options, "negative_options": negative_options})
