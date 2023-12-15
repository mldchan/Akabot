import {
    ButtonInteraction,
    Channel,
    ChatInputCommandInteraction,
    Emoji,
    Guild,
    GuildMember,
    Message,
    Role,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "./type";
import * as fs from "fs";
import { getSelfMember } from "../utilities/useful";

export class MediaOnlyChannelModule implements Module {
    commands: AllCommands = [];
    selfMemberId: string = "";

    async onEmojiCreate(emoji: Emoji): Promise<void> {
    }

    async onEmojiDelete(emoji: Emoji): Promise<void> {
    }

    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {
    }

    async onStickerCreate(sticker: Sticker): Promise<void> {
    }

    async onStickerDelete(sticker: Sticker): Promise<void> {
    }

    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {
    }

    async onSlashCommand(interaction: ChatInputCommandInteraction): Promise<void> {
        console.log(interaction.commandName);
        console.log(interaction.options.getSubcommandGroup(false));
        console.log(interaction.options.getSubcommand(false));
        if (interaction.commandName !== "settings") return;
        if (interaction.options.getSubcommandGroup(false) !== "mediaonlychannels") return;
        switch (interaction.options.getSubcommand(false)) {
            case "set": {
                const result = await commandHandleCreateMediaOnly(interaction);
                if (result === "Set") {
                    const type = interaction.options.getString("type", true) as MediaOnlyChannelTypes;
                    const channel = interaction.options.getChannel("channel", true);
                    await interaction.reply({
                        content: `Set up the channel successfully!\nType: ${type}\nChannel: ${channel.name}`,
                        ephemeral: true
                    });
                    return;
                }

                await interaction.reply({
                    content: result,
                    ephemeral: true
                });
                break;
            }
            case "remove": {
                const result = await commandHandleRemoveMediaOnly(interaction);
                if (result === "Removed") {
                    const channel = interaction.options.getChannel("channel", true);
                    await interaction.reply({
                        content: `Removed the channel successfully!\nChannel: ${channel.name}`,
                        ephemeral: true
                    });
                    return;
                }

                await interaction.reply({
                    content: result,
                    ephemeral: true
                });
                break;
            }
        }
    }

    async onButtonClick(interaction: ButtonInteraction): Promise<void> {
    }

    async onRoleCreate(role: Role): Promise<void> {
    }

    async onRoleEdit(before: Role, after: Role): Promise<void> {
    }

    async onRoleDelete(role: Role): Promise<void> {
    }

    async onChannelCreate(role: Channel): Promise<void> {
    }

    async onChannelEdit(before: Channel, after: Channel): Promise<void> {
    }

    async onChannelDelete(role: Channel): Promise<void> {
    }

    async onMessage(msg: Message): Promise<void> {
        if (msg.author.bot) return ;
        if (!msg.guild) return;
        if (msg.channel.isDMBased()) return;

        const selfMember = getSelfMember(msg.guild);
        if (!selfMember) return;

        if (!msg.channel.permissionsFor(selfMember).has("SendMessages")) return;
        if (!msg.channel.permissionsFor(selfMember).has("ManageMessages")) return;

        const channelType = getChannelType(msg.guild.id, msg.channel.id);
        if (channelType === "none") return;

        if (!msg.attachments.size) {
            if (msg.reference && getChannelReplies(msg.guild.id, msg.channel.id)) {
                const reply = await msg.fetchReference();
                if (reply.attachments.size) return;
            }
            await msg.delete();
            const message = getChannelReplies(msg.guild.id, msg.channel.id) ? "Replies are allowed, but you have to reply to a post." : "You can only send images or videos in this channel.";
            const reply = await msg.channel.send(message);
            await new Promise((resolve) => setTimeout(resolve, 5000));
            await reply.delete();
            return;
        }

        switch (channelType) {
            case "image": {
                // check message attachments are images
                for (const attachment of msg.attachments.values()) {
                    console.log(attachment.contentType);
                    if (!attachment.contentType?.startsWith("image")) {
                        await msg.delete();

                        const reply = await msg.channel.send("You can only send images in this channel.");
                        await new Promise((resolve) => setTimeout(resolve, 5000));
                        await reply.delete();
                        return;
                    }
                }
                break;
            }
            case "video": {
                // check message attachments are videos
                for (const attachment of msg.attachments.values()) {
                    if (!attachment.contentType?.startsWith("video")) {
                        await msg.delete();

                        const reply = await msg.channel.send("You can only send videos in this channel.");
                        await new Promise((resolve) => setTimeout(resolve, 5000));
                        await reply.delete();
                        return;
                    }
                }
                break;
            }
            case "both": {
                // check message attachments are images or videos
                for (const attachment of msg.attachments.values()) {
                    if (!attachment.contentType?.startsWith("image") && !attachment.contentType?.startsWith("video")) {
                        await msg.delete();

                        const reply = await msg.channel.send("You can only send images or videos in this channel.");
                        await new Promise((resolve) => setTimeout(resolve, 5000));
                        await reply.delete();
                        return;
                    }
                }
                break;
            }
        }
    }

    async onMessageDelete(msg: Message): Promise<void> {
    }

    async onMessageEdit(before: Message, after: Message): Promise<void> {
    }

    async onMemberJoin(member: GuildMember): Promise<void> {
    }

    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {
    }

    async onMemberLeave(member: GuildMember): Promise<void> {
    }

    async onGuildAdd(guild: Guild): Promise<void> {
    }

    async onGuildRemove(guild: Guild): Promise<void> {
    }

    async onGuildEdit(before: Guild, after: Guild): Promise<void> {
    }
}

type MediaOnlyChannelTypes = "image" | "video" | "both";

function registerChannel(
    guildID: string,
    channelID: string,
    channelType: MediaOnlyChannelTypes,
    allowReplies: boolean
) {
    if (!fs.existsSync("./data")) fs.mkdirSync("./data");
    if (!fs.existsSync("./data/settings")) fs.mkdirSync("./data/settings");
    if (!fs.existsSync("./data/settings/mediaOnlyChannels")) fs.mkdirSync("./data/settings/mediaOnlyChannels");
    if (!fs.existsSync(`./data/settings/mediaOnlyChannels/${guildID}.json`))
        fs.writeFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, JSON.stringify({}));
    const data = JSON.parse(fs.readFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, "utf-8")) as {
        channels: { id: string; type: MediaOnlyChannelTypes; replies: boolean }[];
    };
    if (!data.channels) data.channels = [];
    if (!data.channels.find((c) => c.id === channelID))
        data.channels.push({ id: channelID, type: channelType, replies: allowReplies });
    fs.writeFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, JSON.stringify(data));
}

function unregisterChannel(guildID: string, channelID: string) {
    if (!fs.existsSync("./data")) fs.mkdirSync("./data");
    if (!fs.existsSync("./data/settings")) fs.mkdirSync("./data/settings");
    if (!fs.existsSync("./data/settings/mediaOnlyChannels")) fs.mkdirSync("./data/settings/mediaOnlyChannels");
    if (!fs.existsSync(`./data/settings/mediaOnlyChannels/${guildID}.json`))
        fs.writeFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, JSON.stringify({}));
    const data = JSON.parse(fs.readFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, "utf-8")) as {
        channels: { id: string; type: MediaOnlyChannelTypes; replies: boolean }[];
    };
    if (!data.channels) data.channels = [];
    data.channels = data.channels.filter((c) => c.id !== channelID);
    fs.writeFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, JSON.stringify(data));
}

function channelRegistered(guildID: string, channelID: string): boolean {
    if (!fs.existsSync("./data")) fs.mkdirSync("./data");
    if (!fs.existsSync("./data/settings")) fs.mkdirSync("./data/settings");
    if (!fs.existsSync("./data/settings/mediaOnlyChannels")) fs.mkdirSync("./data/settings/mediaOnlyChannels");
    if (!fs.existsSync(`./data/settings/mediaOnlyChannels/${guildID}.json`))
        fs.writeFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, JSON.stringify({}));
    const data = JSON.parse(fs.readFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, "utf-8")) as {
        channels: { id: string; type: MediaOnlyChannelTypes; replies: boolean }[];
    };
    if (!data.channels) data.channels = [];
    return !!data.channels.find((c) => c.id === channelID);
}

function getChannelType(guildID: string, channelID: string): MediaOnlyChannelTypes | "none" {
    if (!fs.existsSync("./data")) fs.mkdirSync("./data");
    if (!fs.existsSync("./data/settings")) fs.mkdirSync("./data/settings");
    if (!fs.existsSync("./data/settings/mediaOnlyChannels")) fs.mkdirSync("./data/settings/mediaOnlyChannels");
    if (!fs.existsSync(`./data/settings/mediaOnlyChannels/${guildID}.json`))
        fs.writeFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, JSON.stringify({}));
    const data = JSON.parse(fs.readFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, "utf-8")) as {
        channels: { id: string; type: MediaOnlyChannelTypes; replies: boolean }[];
    };
    if (!data.channels) data.channels = [];
    const channel = data.channels.find((c) => c.id === channelID);
    if (!channel) return "none";
    return channel.type;
}

function getChannelReplies(guildID: string, channelID: string): boolean {
    if (!fs.existsSync("./data")) fs.mkdirSync("./data");
    if (!fs.existsSync("./data/settings")) fs.mkdirSync("./data/settings");
    if (!fs.existsSync("./data/settings/mediaOnlyChannels")) fs.mkdirSync("./data/settings/mediaOnlyChannels");
    if (!fs.existsSync(`./data/settings/mediaOnlyChannels/${guildID}.json`))
        fs.writeFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, JSON.stringify({}));
    const data = JSON.parse(fs.readFileSync(`./data/settings/mediaOnlyChannels/${guildID}.json`, "utf-8")) as {
        channels: { id: string; type: MediaOnlyChannelTypes; replies: boolean }[];
    };
    if (!data.channels) data.channels = [];
    const channel = data.channels.find((c) => c.id === channelID);
    if (!channel) return false;
    return channel.replies;
}

async function commandHandleCreateMediaOnly(
    interaction: ChatInputCommandInteraction
): Promise<"Set" | "No guild" | "Channel not found" | "Channel is not a text channel"> {
    if (!interaction.guild) return "No guild";
    const channel = interaction.options.getChannel("channel", true);
    const type = interaction.options.getString("type", true) as MediaOnlyChannelTypes;
    const allowReplies = interaction.options.getBoolean("allow-replies", false) ?? false;

    const channelRes = interaction.guild.channels.cache.get(channel.id);
    if (!channelRes) return "Channel not found";
    if (!channelRes.isTextBased()) return "Channel is not a text channel";

    if (channelRegistered(interaction.guild.id, channel.id)) unregisterChannel(interaction.guild.id, channel.id);
    registerChannel(interaction.guild.id, channel.id, type, allowReplies);
    return "Set";
}

async function commandHandleRemoveMediaOnly(
    interaction: ChatInputCommandInteraction
): Promise<"Removed" | "No guild" | "Channel not found" | "Channel is not a text channel"> {
    if (!interaction.guild) return "No guild";
    const channel = interaction.options.getChannel("channel", true);

    const channelRes = interaction.guild.channels.cache.get(channel.id);
    if (!channelRes) return "Channel not found";
    if (!channelRes.isTextBased()) return "Channel is not a text channel";

    unregisterChannel(interaction.guild.id, channel.id);
    return "Removed";
}
