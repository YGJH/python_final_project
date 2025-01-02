export interface Message {
    id: string;
    content: string;
    authorId: string;
    timestamp: Date;
}

export interface Command {
    name: string;
    description: string;
    execute: (args: string[]) => Promise<void>;
}