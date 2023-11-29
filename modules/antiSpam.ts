import { ChatInputCommandInteraction, CacheType, ButtonInteraction, Role, Channel, Message, GuildMember, Guild, Emoji, Sticker, EmbedBuilder } from "discord.js";
import { AllCommands, Module } from "./type";
import { ViolationCounters, ViolationCountersMessageData } from "../utilities/violationCounters";
import { getSetting } from "../data/settings";

export class AntiSpamModule implements Module {
    violationCounters = new ViolationCounters();
    async onEmojiCreate(emoji: Emoji): Promise<void> {}
    async onEmojiDelete(emoji: Emoji): Promise<void> {}
    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}
    async onStickerCreate(sticker: Sticker): Promise<void> {}
    async onStickerDelete(sticker: Sticker): Promise<void> {}
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
    commands: AllCommands = [];
    selfMemberId: string = "";
    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {}
    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}
    async onRoleCreate(role: Role): Promise<void> {}
    async onRoleEdit(before: Role, after: Role): Promise<void> {}
    async onRoleDelete(role: Role): Promise<void> {}
    async onChannelCreate(role: Channel): Promise<void> {}
    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}
    async onChannelDelete(role: Channel): Promise<void> {}
    async onMessage(msg: Message<boolean>): Promise<void> {
        if (!msg.guild) return;
        if (msg.author.bot) return;
        const vl = this.violationCounters.vlNew(msg.guild.id, `message${msg.author.id}`, 3000);
        let extraData = this.violationCounters.vlGetExtraData<ViolationCountersMessageData>(msg.guild.id, `message${msg.author.id}`) ?? { messageIDs: [] };
        extraData.messageIDs.push(msg.id);
        this.violationCounters.vlSetExtraData(msg.guild.id, `message${msg.author.id}`, extraData);

        if (vl > 4) {
            await handleMemberAlert(msg);
            const fields: { name: string; value: string }[] = [];
            fields.push({ name: "Bulk delete", value: await handleDeletion(msg, extraData) });
            fields.push({ name: "Timeout", value: await handleTimeout(msg) });
            await handleSendLogMessage(msg, fields);
            this.vlDelete(msg.guild.id, "message");
        }
    }
    vlNew(id: string, arg1: string, arg2: number) {
        throw new Error("Method not implemented.");
    }
    vlGetExtraData<T>(id: string, arg1: string) {
        throw new Error("Method not implemented.");
    }
    vlSetExtraData(id: string, arg1: string, extraData: any) {
        throw new Error("Method not implemented.");
    }
    vlDelete(id: string, arg1: string) {
        throw new Error("Method not implemented.");
    }
    async onMessageDelete(msg: Message<boolean>): Promise<void> {}
    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {}
    async onMemberJoin(member: GuildMember): Promise<void> {}
    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}
    async onMemberLeave(member: GuildMember): Promise<void> {}
    async onGuildAdd(guild: Guild): Promise<void> {}
    async onGuildRemove(guild: Guild): Promise<void> {}
    async onGuildEdit(before: Guild, after: Guild): Promise<void> {}
}
async function handleMemberAlert(msg: Message<boolean>) {
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
async function handleDeletion(msg: Message<boolean>, extraData: ViolationCountersMessageData): Promise<"Deleted" | "Failed; Probably missing permissions" | "Disabled"> {
    const spamDeleteSetting = getSetting(msg.guild!.id, "AntiRaidSpamDelete", "no");
    if (spamDeleteSetting === "yes" && msg.channel.isTextBased() && !msg.channel.isDMBased()) {
        try {
            await msg.channel.bulkDelete(extraData.messageIDs);
            return "Deleted";
        } catch (_) {
            return "Failed; Probably missing permissions";
        }
    } else {
        return "Disabled";
    }
}

/**
 *
 * @param msg Message object
 * @returns The status of the timeout
 */
async function handleTimeout(msg: Message<boolean>): Promise<"10 seconds" | "Failed; Probably missing permissions" | "Disabled"> {
    const spamTimeoutSetting = getSetting(msg.guild!.id, "AntiRaidSpamTimeout", "no");
    if (spamTimeoutSetting === "yes") {
        try {
            await msg.member?.timeout(10000, "Sending messages too fast!");
            return "10 seconds";
        } catch (_) {
            return "Failed; Probably missing permissions";
        }
    } else {
        return "Disabled";
    }
}
async function handleSendLogMessage(msg: Message<boolean>, fields: { name: string; value: string }[]) {
    const logChannelID = getSetting(msg.guild!.id, "loggingChannel", "");
    const logChannel = msg.guild!.channels.cache.get(logChannelID);
    if (logChannel?.isTextBased()) {
        const embed = new EmbedBuilder()
            .setTitle("A member is spamming in this Discord server")
            .addFields({ name: "Member", value: msg.author.username }, { name: "Jump to latest message", value: `[Click here](${msg.url})` }, ...fields)
            .setColor("Red")
            .setTimestamp(new Date());
        await logChannel.send({ embeds: [embed] });
    }
}
