(async function () {
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
  const inputPrevResult = getInput('input-prev-result')

  const inputs = [
    inputRepo,
    inputBranch,
    inputInclude,
    inputExclude,
    inputConfigToml,
    inputParallelSize,
    inputHasYukicoder,
    inputPrevResult,
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

  function buildActionYaml() {
    try {
      const branch = inputBranch.value.trim()
      const parallelSize = parseInt(inputParallelSize.value.trim())
      const configToml = inputConfigToml.value.trim()
      const include = inputInclude.value.trim()
      const exclude = inputExclude.value.trim()

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

        const includeParam = include ? `    ${yamlTextProperty('include', include)}` : '    # include: your-own-include/'
        const excludeParam = exclude ? `    ${yamlTextProperty('exclude', exclude)}` : '    # exclude: your-own-exclude/'
        const configParam = configToml ? `    config: ${configToml}` : '    # config: .verify-helper/config.toml'

        let ojResolve = false

        if (useCpp || usePython) {
          ojResolve = true
        }
        if (useJava) {
          ojResolve = true
          initializeForVerification.push(
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
            '- name: Install dependencies (Go)',
            '  uses: actions/setup-go@v4',
          )
        }
        if (useRuby) {
          ojResolve = true
          initializeForVerification.push(
            '- name: Install dependencies (Ruby)',
            '  uses: ruby/setup-ruby@v1',
            '  with:',
            '    ruby-version: "3.1"',
          )
        }
        if (useNim) {
          ojResolve = true
          initializeForVerification.push(
            '- name: Install dependencies (Nim)',
            '  uses: jiro4989/setup-nim-action@v1',
          )
        }
        if (useHaskel) {
          ojResolve = true
          initializeForVerification.push(
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
            '  uses: baptiste0928/cargo-install@v2',
            '  with:',
            '    crate: cargo-udeps',
            '    cache-key: cargo-udeps-key',
          )
          initializeForVerification.push(
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
            '  run: dotnet run --project $VERIFY_CSPROJ --no-launch-profile --no-build -c Release | tee ${{runner.temp}}/problems.json',
            '  env:',
            '    VERIFY_CSPROJ: YourVerify.csproj',
            '- name: cs-resolve',
            '  uses: competitive-verifier/actions/cs-resolve@v1',
            '  with:',
            '    output-path: verify_files.json',
            '    msbuild-properties: Configuration=Release',
            '    # Specify patterns',
            includeParam,
            excludeParam,
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
            includeParam,
            excludeParam,
            '    # If you have config.toml',
            configParam,
          )
        }

        if (useCpp) {
          initializeForResolving.push(
            '- name: parse-doxygen',
            '  uses: competitive-verifier/actions/parse-doxygen@v1',
            '  with:',
            '    verify-files: verify_files.json',
          )
        }
      }

      const initializeForResolving = []
      const initializeForVerification = []
      initLanguages(initializeForResolving, initializeForVerification)

      let actionYaml = `name: verify
on:
push:
  branches:
    - "${branch}"
workflow_dispatch:
`

      if (inputPrevResult.checked) {
        actionYaml += `    inputs:
    ignore_prev_result:
      type: boolean
      default: false
`
      }

      actionYaml += `
# Sets permissions of the GITHUB_TOKEN to allow deployment to GitHub Pages
permissions:
contents: read
pages: write
id-token: write

# Allow one concurrent deployment
concurrency:
group: "pages"
cancel-in-progress: true

jobs:
setup:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Set up competitive-verifier
      uses: competitive-verifier/actions/setup@v1
      with:
        cache-pip: true

`

      if (initializeForResolving.length > 0) {
        actionYaml += stepDefinition(["      # Initialize your own environment for resolving.", ...initializeForResolving]) + "\n"
      }

      actionYaml += `
    - name: Upload verify_files.json
      uses: competitive-verifier/actions/upload-verify-artifact@v1
      with:
        file: verify_files.json

    - name: Check bundled
      id: test-bundled
      run: |
        echo "count=$(find .competitive-verifier/bundled/ -type f | wc -l)" >> $GITHUB_OUTPUT
    - name: Upload bundled
      uses: actions/upload-artifact@v3
      if: steps.test-bundled.outputs.count > 0
      with:
        name: Bundled-\${{ runner.os }}
        path: .competitive-verifier/bundled
        retention-days: 1

verify:
  runs-on: ubuntu-latest
  needs: [setup]
  env:
    SPLIT_SIZE: "${parseInt(inputParallelSize.value.trim())}"
  strategy:
    matrix:
      # prettier-ignore
      index:
        [${parallelIndexMatrix(parallelSize)}]
  steps:
    - uses: actions/checkout@v4
`
      if (inputPrevResult.checked) {
        actionYaml += `        with:
        fetch-depth: 2147483647

    - name: Restore cached results
      if: \${{ ! inputs.ignore_prev_result }}
      uses: actions/cache/restore@v3
      id: restore-cached-results
      with:
        path: \${{github.workspace}}/merged-result.json
        key: \${{ runner.os }}-verify-result-\${{ github.sha }}
        restore-keys: |
          \${{ runner.os }}-verify-result-
`
      }

      actionYaml += `
    - name: Download verify_files.json
      uses: competitive-verifier/actions/download-verify-artifact@v1

    - name: Set up competitive-verifier
      uses: competitive-verifier/actions/setup@v1
      with:
        cache-pip: true

`
      if (initializeForVerification.length > 0) {
        actionYaml += stepDefinition(["      # Initialize your own environment for verification.", ...initializeForVerification]) + "\n"
      }

      actionYaml += `
    - name: Verify
      uses: competitive-verifier/actions/verify@v1
      with:
        destination: \${{runner.temp}}/result.json
        split-size: \${{ env.SPLIT_SIZE }}
        split-index: \${{ matrix.index }}
        timeout: 1800
`
      if (inputPrevResult.checked) {
        actionYaml += `          prev-result: \${{ steps.restore-cached-results.outputs.cache-hit && 'merged-result.json' || ''}}
`
      }
      if (inputHasYukicoder.checked) {
        actionYaml += `        env:
        YUKICODER_TOKEN: \${{secrets.YUKICODER_TOKEN}}
`
      }


      actionYaml += `
    - name: Upload result artifact
      uses: actions/upload-artifact@v3
      with:
        name: Result-\${{ runner.os }}-\${{ matrix.index }}
        path: \${{runner.temp}}/result.json
        retention-days: 1

docs-and-check:
  runs-on: ubuntu-latest
  needs: [verify]
  outputs:
    upload-pages: \${{steps.upload-pages.outcome == 'success'}}
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 2147483647

    - name: Download verify_files.json and all artifacts
      id: all-artifacts
      uses: competitive-verifier/actions/download-verify-artifact@v1
      with:
        download-all: true
        artifact-root: .artifacts/

    - name: Extract bundled
      shell: bash
      run: |
        rm -rf .competitive-verifier/bundled
        if test -d "$SRCDIR"; then
          mkdir -p .competitive-verifier/
          mv "$SRCDIR" .competitive-verifier/bundled
        else
          echo "$SRCDIR is not exists."
        fi
      env:
        SRCDIR: .artifacts/Bundled-\${{ runner.os }}

    - name: Set up competitive-verifier
      uses: competitive-verifier/actions/setup@v1
      with:
        cache-pip: true
`

      if (inputPrevResult.checked) {
        actionYaml += `
    - name: Merge results
      uses: competitive-verifier/actions/merge-result@v1
      with:
        result-files: \${{ steps.all-artifacts.outputs.artifacts-root }}/Result-*/result.json
        output-path: \${{github.workspace}}/merged-result.json
    - name: Docs
      uses: competitive-verifier/actions/docs@v1
      with:
        verify-result: \${{github.workspace}}/merged-result.json
        destination: _jekyll
        write-summary: true
    - name: Save result
      uses: actions/cache/save@v3
      with:
        path: \${{github.workspace}}/merged-result.json
        key: \${{ runner.os }}-verify-result-\${{ github.sha }}
`
      } else {
        actionYaml += `
    - name: Docs
      uses: competitive-verifier/actions/docs@v1
      with:
        verify-result: \${{ steps.all-artifacts.outputs.artifacts-root }}/Result-*/result.json
        destination: _jekyll
        write-summary: true
`
      }

      actionYaml += `
    - name: Setup Pages
      uses: actions/configure-pages@v3
    - name: Build with Jekyll
      uses: actions/jekyll-build-pages@v1
      with:
        source: _jekyll
        destination: _site
    - name: Upload artifact
      id: upload-pages
      uses: actions/upload-pages-artifact@v2
      with:
        path: _site

    - name: Check
      uses: competitive-verifier/actions/check@v1
      with:
        verify-result: \${{ steps.all-artifacts.outputs.artifacts-root }}/Result-*/result.json
deploy:
  if: (success() || failure()) && github.ref == 'refs/heads/${branch}' && needs.docs-and-check.outputs.upload-pages == 'true'
  needs: docs-and-check
  environment:
    name: github-pages
    url: \${{ steps.deployment.outputs.page_url }}
  runs-on: ubuntu-latest
  steps:
    - name: Deploy to GitHub Pages
      id: deployment
      uses: actions/deploy-pages@v2
`

      return actionYaml.trim()
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
    if (tokens && tokens.toLowerCase().indexOf("yuki") >= 0)
      inputHasYukicoder.checked = true
    else
      inputHasYukicoder.checked = false

    inputPrevResult.checked = urlParams.get("prev-result") != null

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

    if (inputPrevResult.checked) {
      urlParams.set("prev-result", "")
    } else {
      urlParams.delete("prev-result")
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

    for (const link of document.getElementsByClassName('lang-link')) {
      link.href = `${link.dataset.path}?${urlParams}`
    }
    history.replaceState("", "", `${pathname}?${urlParams}`)
  }


  const output = document.getElementById('action-yml')

  async function update() {
    const actionYaml = buildActionYaml()
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
