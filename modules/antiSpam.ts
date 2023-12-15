import {
    ButtonInteraction,
    Channel,
    ChatInputCommandInteraction,
    EmbedBuilder,
    Emoji,
    Guild,
    GuildMember,
    Message,
    Role,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "./type";
import { ViolationCounters, ViolationCountersMessageData } from "../utilities/violationCounters";
import { getSetting } from "../data/settings";
import { getLogChannel, getSelfMember } from "../utilities/useful";

export class AntiSpamModule implements Module {
    violationCounters = new ViolationCounters();
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
        if (!msg.guild) return;
        if (msg.author.bot) return;

        await checkRepeatingWords(msg);

        const vl = this.violationCounters.vlNew(msg.guild.id, `message${msg.author.id}`, 3000);
        let extraData = this.violationCounters.vlGetExtraData<ViolationCountersMessageData>(
            msg.guild.id,
            `message${msg.author.id}`
        ) ?? { messageIDs: [] };
        extraData.messageIDs.push(msg.id);
        this.violationCounters.vlSetExtraData(msg.guild.id, `message${msg.author.id}`, extraData);

        if (vl > 4) {
            await handleMemberAlert(msg);
            const fields: { name: string; value: string }[] = [];
            fields.push({ name: "Bulk delete", value: await handleDeletion(msg, extraData) });
            fields.push({ name: "Timeout", value: await handleTimeout(msg) });
            await handleSendLogMessage(msg, fields);
            this.violationCounters.vlDelete(msg.guild.id, "message");
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

async function handleMemberAlert(msg: Message) {
    const spamSendAlert = getSetting(msg.guild!.id, "AntiRaidSpamSendAlert", "no");
    if (spamSendAlert === "yes") {
        await msg.channel.send(`<@${msg.author.id}>, You are sending messages too fast!`);
    }
}

/**
 *
 * @param msg The message object
 * @param extraData The extra data that is gotten from the ViolationCounters class
 * @returns The status of the deletion
 */
async function handleDeletion(
    msg: Message,
    extraData: ViolationCountersMessageData
): Promise<"Deleted" | "Missing Permissions" | "Disabled"> {
    if (msg.channel.isDMBased()) return "Disabled";
    if (getSetting(msg.guild!.id, "AntiRaidSpamDelete", "no") === "no") return "Disabled";

    const selfMember = getSelfMember(msg.guild!);
    if (!selfMember?.permissionsIn(msg.channel).has("ManageMessages")) {
        return "Missing Permissions";
    }

    await msg.channel.bulkDelete(extraData.messageIDs);
    return "Deleted";
}

/**
 *
 * @param msg Message object
 * @returns The status of the timeout
 */
async function handleTimeout(
    msg: Message
): Promise<"10 seconds" | "Missing Permissions" | "Disabled"> {
    if (msg.channel.isDMBased()) return "Disabled";
    if (!msg.member) return "Disabled";
    if (getSetting(msg.guild!.id, "AntiRaidSpamTimeout", "no") === "no") return "Disabled";
    const selfMember = getSelfMember(msg.guild!);
    if (!selfMember) return "Disabled";
    if (!selfMember.permissionsIn(msg.channel).has("ManageRoles")) {
        return "Missing Permissions";
    }
    if (selfMember.roles.highest.comparePositionTo(msg.member.roles.highest) <= 0) {
        return "Missing Permissions";
    }

    await msg.member.timeout(10000, "Sending messages too fast!");
    return "10 seconds";
}

async function handleSendLogMessage(msg: Message, fields: { name: string; value: string }[]) {
    const logChannel = getLogChannel(msg.guild!);
    const embed = new EmbedBuilder()
        .setTitle("A member is spamming in this Discord server")
        .addFields(
            { name: "Member", value: msg.author.username },
            { name: "Jump to latest message", value: `[Click here](${msg.url})` },
            ...fields
        )
        .setColor("Red")
        .setTimestamp(new Date());
    await logChannel?.send({ embeds: [embed] });
}

async function checkRepeatingWords(msg: Message) {
    if (msg.channel.isDMBased()) return;
    const selfMember = getSelfMember(msg.guild!);
    if (!selfMember) return;
    if (!selfMember.permissionsIn(msg.channel).has("ManageMessages")) return;
    if (msg.channel.isDMBased()) return;
    const words = msg.content
        .replaceAll(/[.,\-_\\/]/g, "")
        .replaceAll("\n", "")
        .split(/\s/g)
        .flat();
    if (words.length < 3) return;
    const wordCount: { [key: string]: number } = {};
    for (const word of words) {
        if (wordCount[word]) {
            wordCount[word]++;
        } else {
            wordCount[word] = 1;
        }
    }

    console.log("checkRepeatingWords", Object.keys(wordCount).length, words.length);
    const threshold = Math.max(1 / (words.length / 2), 0.1);
    console.log("checkRepeatingWords", threshold);
    const percentage = Object.keys(wordCount).length / words.length;
    if (percentage < threshold) {
        console.log("checkRepeatingWords", "spam detected");
        try {
            await msg.delete();
        } catch (_) {
        }
    }
    console.log("checkRepeatWords", "percentage", percentage);
}
