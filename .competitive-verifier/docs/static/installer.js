(async function () {
    const templatePromise = fetch('action-template.yml').then(p => p.text())


    /**
     *  @param {string[]} lines
     *  @return {string} string with head space
     */
    function stepDefinition(lines) {
        return lines.join('\n      ')
    }

    const inputStringHeadSpace = ' '.repeat(16)

    /**
     *  @param {string} id
     *  @return {HTMLInputElement} getElementById
     */
    const getInput = (id) => document.getElementById(id)

    /**
     *  @param {string} name
     *  @param {string} text
     *  @return {string} string with head space
     */
    function yamlTextProperty(name, text) {
        const arr = text.split(/\r?\n/)
        arr.splice(0, 0, `${name}: |`)
        return arr.join('\n' + inputStringHeadSpace)
    }

    /**
     *  @param {number} size
     *  @return {string} yaml array
     */
    function parallelIndexMatrix(size) {
        if (isNaN(size)) {
            throw new Error('Parallel size must be integer.')
        } else if (size < 1) {
            throw new Error('Parallel size must be positive.')
        } else if (size > 100) {
            throw new Error('Parallel size must be 100 or less.')
        }
        const lines = []
        const separator = ',\n           '
        const length = (size - 1).toString().length
        for (let start = 0; start < size; start += 10) {
            const array = Array(Math.min(size - start, 10))

            for (let i = 0; i < array.length; i++) {
                array[i] = `"${(start + i).toString().padStart(length, '0')}"`
            }
            lines.push(array.join(', '))
        }

        return lines.join(separator)
    }

    const urlParams = new URLSearchParams(location.search)
    const pathname = location.pathname

    const inputRepo = getInput('input-repo')
    const inputBranch = getInput('input-branch')
    const inputHasYukicoder = getInput('input-yukicoder')
    const inputInclude = getInput('input-include')
    const inputExclude = getInput('input-exclude')
    const inputConfigToml = getInput('input-config-toml')
    const inputParallelSize = getInput('input-parallel-size')

    const inputs = [
        inputRepo,
        inputBranch,
        inputInclude,
        inputExclude,
        inputConfigToml,
        inputParallelSize,
        inputHasYukicoder,
    ]

    const inputLangCpp = getInput('input-lang-cpp')
    const inputLangPython = getInput('input-lang-python')
    const inputLangRust = getInput('input-lang-rust')
    const inputLangJava = getInput('input-lang-java')
    const inputLangGo = getInput('input-lang-go')
    const inputLangRuby = getInput('input-lang-ruby')
    const inputLangNim = getInput('input-lang-nim')
    const inputLangHaskel = getInput('input-lang-haskel')
    const inputLangCSharp = getInput('input-lang-csharp')
    const inputLangs = [
        inputLangCpp,
        inputLangPython,
        inputLangRust,
        inputLangJava,
        inputLangGo,
        inputLangRuby,
        inputLangNim,
        inputLangHaskel,
        inputLangCSharp,
    ]

    /**
     *  @param {string[]} initializeForResolving
     *  @param {string[]} initializeForVerification
     *  @returns {boolean} use oj-resolve
     */
    function initLanguages(initializeForResolving, initializeForVerification) {
        const useCpp = inputLangCpp.checked
        const usePython = inputLangPython.checked
        const useRust = inputLangRust.checked
        const useJava = inputLangJava.checked
        const useGo = inputLangGo.checked
        const useRuby = inputLangRuby.checked
        const useNim = inputLangNim.checked
        const useHaskel = inputLangHaskel.checked
        const useCSharp = inputLangCSharp.checked


        let ojResolve = false

        if (useCpp || usePython) {
            ojResolve = true
        }
        if (useJava) {
            ojResolve = true
            initializeForVerification.push(
                '# required only if you want to verify Java code',
                '- name: Install dependencies (Java)',
                '  uses: actions/setup-java@v3',
                '  with:',
                '    distribution: "temurin"',
                '    java-version: "11"',
            )
        }
        if (useGo) {
            ojResolve = true
            initializeForVerification.push(
                '# required only if you want to verify Go code',
                '- name: Install dependencies (Go)',
                '  uses: actions/setup-go@v3',
            )
        }
        if (useRuby) {
            ojResolve = true
            initializeForVerification.push(
                '# required only if you want to verify Ruby code',
                '- name: Install dependencies (Ruby)',
                '  uses: ruby/setup-ruby@v1',
                '  with:',
                '    ruby-version: "3.1"',
            )
        }
        if (useNim) {
            ojResolve = true
            initializeForVerification.push(
                '# required only if you want to verify Nim code',
                '- name: Install dependencies (Nim)',
                '  uses: jiro4989/setup-nim-action@v1',
            )
        }
        if (useHaskel) {
            ojResolve = true
            initializeForVerification.push(
                '# required only if you want to verify Haskell code',
                '- name: Install dependencies (Haskell)',
                '  uses: haskell/actions/setup@v2',
            )
        }
        if (useRust) {
            ojResolve = true
            initializeForResolving.push(
                '# required only if you set `languages.rust.list_dependencies_backend.kind` to `"cargo-udeps"`',
                '- name: Set up Rust (nightly)',
                '  uses: dtolnay/rust-toolchain@stable',
                '  with:',
                '    toolchain: nightly',
                '    targets: x86_64-unknown-linux-gnu',
                '- name: Install cargo-udeps for Rust',
                '  uses: baptiste0928/cargo-install@v1',
                '  with:',
                '    crate: cargo-udeps',
                '    cache-key: cargo-udeps-key',
            )
            initializeForVerification.push(
                '# required only if you want to verify Rust',
                '- name: Set up Rust (1.42.0)',
                '  uses: dtolnay/rust-toolchain@stable',
                '  with:',
                '    toolchain: "1.42.0"',
                '    targets: x86_64-unknown-linux-gnu',
            )
        }
        if (useCSharp) {
            const setup = [
                '- name: Setup .NET SDK',
                '  uses: actions/setup-dotnet@v3',
                '  with:',
                '    dotnet-version: |',
                '      7.0.x',
                '      3.1.x',
                '- name: Build',
                '  run: dotnet build $WORKFLOW_BUILD_SLN -c Release',
                '  env:',
                '    WORKFLOW_BUILD_SLN: YourSolution.sln',
            ]

            initializeForResolving.push(...setup,
                '- name: setup CompetitiveVerifierCsResolver',
                '  run: dotnet tool install -g CompetitiveVerifierCsResolver',
                '# required only if you have unit test.',
                '- name: Unit test',
                '  run: dotnet test $UNITTEST_CSPROJ --logger "CompetitiveVerifier;OutDirectory=${{runner.temp}}/VerifierCsUnitTestResult" --no-build  -c Release',
                '  env:',
                '    UNITTEST_CSPROJ: YourUnittest.csproj',
                '- name: Resolve',
                '  run: dotnet run --project $VERIFY_CSPROJ --no-build -c Release | tee ${{runner.temp}}/problems.json',
                '  env:',
                '    VERIFY_CSPROJ: YourVerify.csproj',
                '- name: cs-resolve',
                '  uses: competitive-verifier/actions/cs-resolve@v1',
                '  with:',
                '    output-path: verify_files.json',
                '    # Specify patterns',
                '    # include: your-own-include/',
                '    # exclude: your-own-exclude/',
                '    unittest-result: ${{runner.temp}}/VerifierCsUnitTestResult/*.csv',
                '    problems: ${{runner.temp}}/problems.json',
            )
            initializeForVerification.push(...setup)
        }

        if (ojResolve) {
            initializeForResolving.push(
                '- name: oj-resolve',
                '  uses: competitive-verifier/actions/oj-resolve@v1',
                '  with:',
                '    output-path: verify_files.json',
                '    # Specify patterns',
                '    # include: your-own-include/',
                '    # exclude: your-own-exclude/',
                '    # If you have config.toml',
                '    # config: .verify-helper/config.toml',
            )
        }
    }

    async function getActionYaml() {
        try {
            const template = await templatePromise
            const branch = inputBranch.value.trim()
            const configToml = inputConfigToml.value.trim()
            const include = inputInclude.value.trim()
            const exclude = inputExclude.value.trim()
            const parallelSize = parseInt(inputParallelSize.value.trim())

            let resultYaml = template
                .replaceAll('{{{branch}}}', branch)
                .replaceAll('"{{{parallel_size}}}"', parallelSize.toString())
                .replaceAll('"{{{parallel_indexes}}}"', parallelIndexMatrix(parallelSize))

            const initializeForResolving = ["# Initialize your own environment for resolving."]
            const initializeForVerification = ["# Initialize your own environment for verification."]

            if (inputHasYukicoder.checked) {
                resultYaml = resultYaml.replaceAll("# YUKICODER_TOKEN: ${{secrets.YUKICODER_TOKEN}}", "  YUKICODER_TOKEN: ${{secrets.YUKICODER_TOKEN}}")
            }

            initLanguages(initializeForResolving, initializeForVerification)
            if (initializeForResolving.length > 1) {
                resultYaml = resultYaml.replaceAll(initializeForResolving[0], stepDefinition(initializeForResolving))
            }
            if (initializeForVerification.length > 1) {
                resultYaml = resultYaml.replaceAll(initializeForVerification[0], stepDefinition(initializeForVerification))
            }

            if (configToml) {
                resultYaml = resultYaml.replaceAll('# config: .verify-helper/config.toml', `config: ${configToml}`)
            }

            if (include) {
                resultYaml = resultYaml.replaceAll('# include: your-own-include/', yamlTextProperty('include', include))
            }
            if (exclude) {
                resultYaml = resultYaml.replaceAll('# exclude: your-own-exclude/', yamlTextProperty('exclude', exclude))
            }

            return resultYaml.trim()
        } catch (error) {
            return error
        }
    }

    function loadQuery() {
        const setToInput = (node, name) => {
            const value = urlParams.get(name)
            if (value)
                node.value = value
        }
        setToInput(inputRepo, "repository")
        setToInput(inputInclude, "include")
        setToInput(inputExclude, "exclude")
        setToInput(inputConfigToml, "configToml")
        setToInput(inputParallelSize, "parallel")

        const tokens = urlParams.get("tokens")
        if (tokens && tokens.toLowerCase() == "yuki")
            inputHasYukicoder.checked = true
        else
            inputHasYukicoder.checked = false

        const loadLanguages = () => {
            const input = urlParams.get("langs")
            if (!input) return
            const langs = new Set(input.split('|').map(s => s.toLowerCase()))

            inputLangCpp.checked = langs.has("cpp")
            inputLangPython.checked = langs.has("python")
            inputLangRust.checked = langs.has("rust")
            inputLangJava.checked = langs.has("java")
            inputLangGo.checked = langs.has("go")
            inputLangRuby.checked = langs.has("ruby")
            inputLangNim.checked = langs.has("nim")
            inputLangHaskel.checked = langs.has("haskel")
            inputLangCSharp.checked = langs.has("csharp")
        }

        loadLanguages()
    }
    function updateQuery() {
        const readInput = (node, name) => {
            const value = node.value
            if (value)
                urlParams.set(name, value)
            else
                urlParams.delete(name)
        }
        readInput(inputRepo, "repository")
        readInput(inputInclude, "include")
        readInput(inputExclude, "exclude")
        readInput(inputConfigToml, "configToml")
        readInput(inputParallelSize, "parallel")

        if (inputHasYukicoder.checked) {
            urlParams.set("tokens", "yuki")
        } else {
            urlParams.set("tokens", "")
        }

        const langs = []
        if (inputLangCpp.checked) langs.push("cpp")
        if (inputLangPython.checked) langs.push("python")
        if (inputLangRust.checked) langs.push("rust")
        if (inputLangJava.checked) langs.push("java")
        if (inputLangGo.checked) langs.push("go")
        if (inputLangRuby.checked) langs.push("ruby")
        if (inputLangNim.checked) langs.push("nim")
        if (inputLangHaskel.checked) langs.push("haskel")
        if (inputLangCSharp.checked) langs.push("csharp")
        urlParams.set("langs", langs.join("|"))

        history.replaceState("", "", `${pathname}?${urlParams}`)
    }


    const output = document.getElementById('action-yml')

    async function update() {
        const actionYaml = await getActionYaml()
        output.innerHTML = actionYaml
        hljs.highlightElement(output)

        const [_, repoUser, repoName] = parseRepository() || [undefined, undefined, undefined]
        const repoRoot = `https://github.com/${repoUser}/${repoName}`
        {
            const url = `${repoRoot}/settings/pages`
            const outputSettingsPagesLink = document.getElementById('settings-pages')
            outputSettingsPagesLink.href = url
        }
        {
            const outputCreateActionLink = document.getElementById('create-action')
            // New action
            const createUrl = `${repoRoot}/new/${inputBranch.value}/.github/workflows?filename=verify.yml&value=${encodeURIComponent('# Paste action')}`
            outputCreateActionLink.href = createUrl

            const editUrl = `${repoRoot}/edit/${inputBranch.value}/.github/workflows/verify.yml`;
            (async function () {
                const editResponse = await fetch(`https://api.github.com/repos/${repoUser}/${repoName}/contents/.github/workflows/verify.yml`)
                if (editResponse.ok)
                    outputCreateActionLink.href = editUrl
            })()
        }
        {
            const badgeVerifyRaw = document.getElementById('badge-verify-raw')
            const badgeVerifyLink = document.getElementById('badge-verify-link')
            const badgeVerifyImg = document.getElementById('badge-verify-img')
            const link = repoRoot + "/actions"
            const img = repoRoot + "/workflows/verify/badge.svg"
            badgeVerifyRaw.value = `[![Actions Status](${img})](${link})`
            badgeVerifyLink.href = link
            badgeVerifyImg.src = img
        }
        {
            const badgePagesRaw = document.getElementById('badge-pages-raw')
            const badgePagesLink = document.getElementById('badge-pages-link')
            const badgePagesImg = document.getElementById('badge-pages-img')
            const link = `https://${repoUser}.github.io/${repoName}`
            const img = "https://img.shields.io/static/v1?label=GitHub+Pages&message=+&color=brightgreen&logo=github"
            badgePagesRaw.value = `[![GitHub Pages](${img})](${link})`
            badgePagesLink.href = link
            badgePagesImg.src = img
        }
        updateQuery()
    }

    async function retrieveDefaultBranch() {
        const [_, repoUser, repoName] = parseRepository()
        if (!repoName) return
        const url = `https://api.github.com/repos/${repoUser}/${repoName}`
        const response = await fetch(url).then(r => r.json())
        if (response.default_branch) {
            inputBranch.value = response.default_branch
        }
    }

    function parseRepository() {
        let repsitory = inputRepo.value.trim()
        if (repsitory.endsWith('.git')) {
            repsitory = repsitory.substring(0, repsitory.length - 4)
        }
        let found = repsitory.match(/github.com\/([^\/]+)\/([^\/]+)$/)
        if (!found) {
            found = repsitory.match(/^([^\/]+)\/([^\/]+)$/)
        }
        return found
    }

    inputRepo.addEventListener('change', retrieveDefaultBranch)
    inputRepo.addEventListener('keyup', retrieveDefaultBranch)
    for (const input of inputs) {
        input.addEventListener('change', update)
        input.addEventListener('keyup', update)
    }
    for (const lang of inputLangs) {
        lang.addEventListener('change', update)
    }

    loadQuery()
    await retrieveDefaultBranch()
    await update()
})()