// encrypt on submit
$('#sensitive').submit((event) => {
    event.preventDefault()  // prevents form submission before encryption
    RSAEncrypt()
})

function encryptForm(crypto) {
    const form = document.getElementById('sensitive')
    Array.from(form.getElementsByTagName('input')).forEach(input => {
        if(input.type == 'password') {
            input.value = crypto.encrypt(input.value)
        }
    });
}

function RSAEncrypt() {
    // retrieve public key from server
    const xhttp = new XMLHttpRequest()

    xhttp.open('PUT', `${window.location.origin}/key/`)
    xhttp.setRequestHeader('X-CSRFToken', shortcuts.getCSRFToken())
    
    xhttp.onreadystatechange = () => {
        if(xhttp.readyState == 4 && xhttp.status == 200) {
            // key retrieved, encrypt credentials
            const crypto = new JSEncrypt()
            crypto.setKey(xhttp.response)
            encryptForm(crypto)

            // submit form
            document.getElementById('sensitive').submit()
        }
    }
    xhttp.send()
}
