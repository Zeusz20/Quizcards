var activeId = 0

init()


function init() {
    const nextButton = document.getElementById('next-btn')
    shortcuts.hideElement(nextButton)
    
    nextButton.onclick = () => {
        shortcuts.hideElement(nextButton)
        showNextQuestion()
    }

    // hide retry button
    const retryButton = document.getElementById('retry-btn')
    shortcuts.hideElement(retryButton)

    showNextQuestion()
}

/** Displays the next question in the quiz. */
function showNextQuestion() {
    const wrapper = document.getElementById('wrapper')
    const questions = shortcuts.getElementsByLabel('question')

    wrapper.innerHTML = questions[activeId].innerHTML
    bind(questions[activeId])
    
    activeId++
}

/** Displays "next button" of "retry button" depending on quiz progression. */
function showNav() {
    const nextButton = document.getElementById('next-btn')
    const retryButton = document.getElementById('retry-btn')
    const questions = shortcuts.getElementsByLabel('question')
    
    if(activeId + 1 < questions.length) {
        shortcuts.showElement(nextButton)
    }
    else {
        shortcuts.showElement(retryButton)
    }
}

/** Adds onclick funtionality to answer nodes, so user can choose and click an answer. */
function bind(quiz) {
    const answers = document.getElementsByName('answer')

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

/** After answering unbind any functionality from answer nodes. */
function unbind(answers) {
    answers.forEach(answer => {
        answer.onclick = null
    })
}

/** Colors the respective answer green. */
function success(answer) {
    answer.classList.remove('btn-outline-secondary')
    answer.classList.add('btn-success')
}

/** Colors the respective answer red. */
function fail(answer) {
    answer.classList.remove('btn-outline-secondary')
    answer.classList.add('btn-danger')
}

/** Finds the correct answer node which matches the question. */
function findCorrectAnswer(quiz) {
    const answers = Array.from(document.getElementsByName('answer'))

    for(let i=0; i < answers.length; i++) {
        const answer = answers[i]
        if(answer.value == 'True') {
            return answer
        }
    }

    return null
}
