from random import sample, shuffle
from .models import Card, Deck

_DEFAULT_SETTINGS = {
    'start_with': 'definition',
    'answer_with': 'term',
    'show_images': True,
}


def get_settings(post=None):
    if not post:
        return _DEFAULT_SETTINGS

    return {
        'start_with': post.get('start-with') or 'definition',
        'answer_with': post.get('answer-with') or 'term',
        'show_images': post.get('show-images') is not None,
    }


def _construct(card, face, **kwargs):
    struct = {
        'text': getattr(card, face),
        'image': getattr(card, face + '_image')
    }
    struct.update(kwargs)
    return struct


def generate_questions(uuid, answer_with):
    deck = Deck.objects.get(uuid=uuid)
    cards = list(Card.objects.filter(deck=deck))  # has to be list in order to work with the random module

    questions = list()
    num_of_choices = min(len(cards), 4)
    opposite_face = 'definition' if answer_with == 'term' else 'term'

    for card in cards:
        question = {
            'question': _construct(card, opposite_face),
            'answers': [
                _construct(card, answer_with, correct=True),
            ]
        }

        # do-while would be perfect
        wrong_answers = sample(cards, num_of_choices - 1)
        while card in wrong_answers:
            wrong_answers = sample(cards, num_of_choices - 1)

        for wrong_card in wrong_answers:
            wrong_answer = _construct(wrong_card, answer_with, correct=False)
            question['answers'].append(wrong_answer)

        shuffle(question['answers'])
        questions.append(question)

    shuffle(questions)
    return questions
