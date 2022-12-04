document.getElementsByClassName('hljs')

for (const code of document.querySelectorAll('.hljs code')) {
    hljs.highlightElement(code)
}

for (const btn of document.getElementsByClassName('code-copy-btn')) {
    btn.addEventListener('click', async function () {
        const preText = this.closest('.code').querySelector('.hljs:not(.disable) code').innerText
        navigator.clipboard.writeText(preText)

        this.classList.remove("hint--disable")
        await new Promise(r => setTimeout(r, 700))
        this.classList.add("hint--disable")
    })
}

for (const btn of document.getElementsByClassName('code-copy-btn')) {
    btn.addEventListener('click', async function () {
        const preText = this.closest('.code').querySelector('.hljs:not(.disable) code').innerText
        navigator.clipboard.writeText(preText)

        this.classList.remove("hint--disable")
        await new Promise(r => setTimeout(r, 700))
        this.classList.add("hint--disable")
    })
}

for (const btn of document.getElementsByClassName('code-toggle-btn')) {
    btn.addEventListener('click', function () {
        for (const btn of document.getElementsByClassName('code-toggle-btn')) {
            btn.classList.remove('selected')
        }
        this.classList.add('selected')

        const targetId = this.dataset.target
        for (const hljs of document.getElementsByClassName('hljs')) {
            if (hljs.tagName.toLowerCase() === 'pre')
                hljs.classList.add('disable')
        }
        document.getElementById(targetId).classList.remove('disable')
    })
}
