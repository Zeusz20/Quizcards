var activeId = -1

init()


function init() {
    const nextButton = document.getElementById('next')
    nextButton.style.visibility = 'hidden'
    nextButton.onclick = () => {
        nextButton.style.visibility = 'hidden'
        showNextQuestion()
    }

    // hide retry button
    document.getElementById('retry').style.visibility = 'hidden'

    showNextQuestion()
}

/* displays the next question in the quiz */
function showNextQuestion() {
    activeId++

    const quizes = Array.from(document.getElementsByName('quiz'))
    const active = document.getElementById('active-quiz')

    active.innerHTML = quizes[activeId].innerHTML
    bind(active)
}

/* displays "next button" of "retry button" depending on quiz progression */
function showNav() {
    const nextButton = document.getElementById('next')
    const retryButton = document.getElementById('retry')
    
    if(activeId + 1 < document.getElementsByName('quiz').length) {
        nextButton.style.visibility = 'visible'
    }
    else {
        retryButton.style.visibility = 'visible'
    }
}

/* adds onclick funtionality to answer nodes, so user can choose and click an answer */
function bind(quiz) {
    const answers = Array.from(quiz.getElementsByTagName('button'))

    answers.forEach(answer => {
        answer.onclick = () => {
            if(answer.value == 'True') {
                success(answer)
            }
            else {
                fail(answer)
                success(findCorrectAnswer(quiz))
            }

            unbind(answers)
            showNav()
        }
    })
}

/* after answering unbind any functionality from answer nodes */
function unbind(answers) {
    answers.forEach(answer => {
        answer.onclick = null
    })
}

/* colors the respective answer green */
function success(answer) {
    answer.classList.remove('btn-outline-secondary')
    answer.classList.add('btn-success')
}

/* colors the respective answer red */
function fail(answer) {
    answer.classList.remove('btn-outline-secondary')
    answer.classList.add('btn-danger')
}

/* finds the correct answer node which matches the question */
function findCorrectAnswer(quiz) {
    const answers = Array.from(quiz.getElementsByTagName('button'))

    for(let i=0; i < answers.length; i++) {
        const answer = answers[i]
        if(answer.value == 'True') {
            return answer
        }
    }

    return null
}
