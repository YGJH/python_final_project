function setRoutes(app) {
    const { IndexController } = require('../controllers/index');

    const indexController = new IndexController();

    app.post('/command', (req, res) => {
        const command = req.body.command;
        indexController.handleCommand(command)
            .then(response => res.json({ response }))
            .catch(error => res.status(500).json({ error: error.message }));
    });
}

module.exports = { setRoutes };