from random import sample, shuffle
from .models import Card, Deck


def generate_questions(uuid, start_with):
    deck = Deck.objects.get(uuid=uuid)
    cards = list(Card.objects.filter(deck=deck))

    questions = list()
    num_of_choices = min(len(cards), 4)
    opposite_face = 'definition' if start_with == 'term' else 'term'

    for card in cards:
        question = {
            'question': {
                'text': getattr(card, start_with),
                'image': getattr(card, start_with + '_image'),
            },
            'answers': [
                {
                    'text': getattr(card, opposite_face),
                    'image': getattr(card, opposite_face + '_image'),
                    'correct': True,
                },
            ]
        }

        # do-while would be perfect
        wrong_answers = sample(cards, num_of_choices - 1)
        while card in wrong_answers:
            wrong_answers = sample(cards, num_of_choices - 1)

        for wrong in wrong_answers:
            question['answers'].append({
                'text': getattr(wrong, opposite_face),
                'image': getattr(wrong, opposite_face + '_image'),
                'correct': False,
            })

        shuffle(question['answers'])
        questions.append(question)

    shuffle(questions)
    return questions
