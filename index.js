const express = require('express')
const { spawn } = require('child_process')
const app = express()
const port = 8080

app.get('/', (req, res) => {
  let dataToSend
  let largeDataSet = []
  const python = spawn('python', ['main.py'])

  python.stdout.on('data', function (data) {
    console.log('Pipe data from python script ...')
    largeDataSet.push(data)
  })

  python.on('close', (code) => {
    console.log(`child process close all stdio with code ${code}`)
    res.status(200).send({data: largeDataSet.join('')})
  })
})

app.listen(port, () => {
  console.log(`App listening on port ${port}!`)
})
