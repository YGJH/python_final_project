class IndexController {
    constructor() {
        // 初始化控制器
    }

    handleCommand(command: string, args: string[]): string {
        switch (command) {
            case 'hello':
                return this.sayHello(args);
            case 'help':
                return this.showHelp();
            default:
                return '未知的指令。請使用 `help` 獲取可用指令列表。';
        }
    }

    private sayHello(args: string[]): string {
        const name = args.length > 0 ? args[0] : '世界';
        return `你好，${name}！`;
    }

    private showHelp(): string {
        return '可用指令：\n1. hello [name] - 打招呼\n2. help - 顯示可用指令';
    }
}

export default IndexController;