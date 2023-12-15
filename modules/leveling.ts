import {
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction,
    EmbedBuilder,
    Emoji,
    Guild,
    GuildMember,
    Message,
    Role,
    SlashCommandBuilder,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "./type";
import { addPointsToUser, getUserLevel, getUserPoints, getUserRequirementForNextLevel } from "../data/leveling";
import { getSetting } from "../data/settings";
import { getSelfMember } from "../utilities/useful";

function getFormattedDate() {
    const date = new Date();
    return `${date.getUTCFullYear()}/${date.getUTCMonth()}/${date.getUTCDate()} ${date.getUTCHours()}:${date.getUTCMinutes()}:${date.getUTCSeconds()} UTC`;
}

async function handleLevelUp(msg: Message<boolean>, selfMember: GuildMember, levelBefore: number, xpBefore: number, levelAfter: number, xpAfter: number) {
    console.log("leveling", "onMessage", "level up");
    const levelingChannelId = getSetting(msg.guild!.id, "levelingChannel", "");
    const levelingChannel = msg.guild!.channels.cache.get(levelingChannelId);
    if (!levelingChannel) return;
    if (!levelingChannel.isTextBased()) return;
    if (!levelingChannel.permissionsFor(selfMember).has("SendMessages")) return;
    const embed = new EmbedBuilder()
        .setTitle(`Level Up - ${msg.author.username}`)
        .setDescription(
            `${msg.author.username} has leveled up from level ${levelBefore} (${xpBefore} XP) to level ${levelAfter} (${xpAfter} XP)`
        )
        .setColor("Green")
        .setFooter({
            text: getFormattedDate()
        });
    console.log("leveling", "onMessage", "sending message");
    await levelingChannel.send({
        content: `<@${msg.author.id}>`,
        embeds: [embed]
    });
}

export class LevelingModule implements Module {
    commands: AllCommands = [
        new SlashCommandBuilder().setName("level").setDescription("Get your current level").setDMPermission(false),
        new SlashCommandBuilder().setName("rank").setDescription("Get your current level").setDMPermission(false)
    ];
    selfMemberId: string = "";

    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        if (interaction.commandName !== "level" && interaction.commandName !== "rank") return;
        if (!interaction.guild) return;
        const points = getUserPoints(interaction.guild.id, interaction.user.id);
        const level = getUserLevel(points);
        const pointsToNext = getUserRequirementForNextLevel(points);
        const embed = new EmbedBuilder()
            .setTitle(`Level - ${interaction.user.displayName}`)
            .setDescription(
                `You are currently on level ${level} (${points} XP)\nYou need ${
                    pointsToNext - points
                } XP for next level.`
            )
            .setFooter({
                text: getFormattedDate()
            });
        await interaction.reply({
            embeds: [embed]
        });
    }

    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {
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

    async onMessage(msg: Message<boolean>): Promise<void> {
        if (!msg.guild) return;
        const selfMember = getSelfMember(msg.guild);
        if (!selfMember) return;
        if (msg.author.bot) return;
        const xpBefore = getUserPoints(msg.guild.id, msg.author.id);
        const levelBefore = getUserLevel(xpBefore);
        console.log("leveling", "onMessage", "xpBefore", xpBefore, "levelBefore", levelBefore);
        addPointsToUser(msg.guild.id, msg.author.id, msg.content.length);
        console.log("leveling", "onMessage", "added points", msg.content.length);
        const xpAfter = getUserPoints(msg.guild.id, msg.author.id);
        const levelAfter = getUserLevel(xpAfter);
        console.log("leveling", "onMessage", "xpAfter", xpAfter, "levelAfter", levelAfter);
        if (levelBefore !== levelAfter) {
            await handleLevelUp(msg, selfMember, levelBefore, xpBefore, levelAfter, xpAfter);
        }
    }

    async onMessageDelete(msg: Message<boolean>): Promise<void> {
    }

    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {
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
}
