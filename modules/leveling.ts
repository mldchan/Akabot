import {
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction,
    Client,
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
import * as fs from "fs";

function getFormattedDate() {
    const date = new Date();
    return `${date.getUTCFullYear()}/${date.getUTCMonth()}/${date.getUTCDate()} ${date.getUTCHours()}:${date.getUTCMinutes()}:${date.getUTCSeconds()} UTC`;
}

async function handleLevelUp(
    msg: Message<boolean>,
    selfMember: GuildMember,
    levelBefore: number,
    xpBefore: number,
    levelAfter: number,
    xpAfter: number
) {
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

async function handleLevelCommand(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;
    const points = getUserPoints(interaction.guild.id, interaction.user.id);
    const level = getUserLevel(points);
    const pointsToNext = getUserRequirementForNextLevel(points);
    const embed = new EmbedBuilder()
        .setTitle(`Level - ${interaction.user.displayName}`)
        .setDescription(
            `You are currently on level ${level} (${points} XP)\nYou need ${pointsToNext - points} XP for next level.`
        )
        .setFooter({
            text: getFormattedDate()
        });
    await interaction.reply({
        embeds: [embed]
    });
}

type LevelingReward = {
    level: number;
    role: string;
};

function loadRewards(guildID: string): LevelingReward[] {
    if (!fs.existsSync(`./data/${guildID}/levelingRewards.json`)) {
        fs.writeFileSync(`./data/${guildID}/levelingRewards.json`, JSON.stringify([]));
        return [];
    }
    const rewards = fs.readFileSync(`./data/${guildID}/levelingRewards.json`, "utf-8");
    return JSON.parse(rewards);
}

function saveRewards(guildID: string, rewards: LevelingReward[]) {
    fs.writeFileSync(`./data/${guildID}/levelingRewards.json`, JSON.stringify(rewards));
}

function addRoleReward(guildID: any, roleID: any, atLevel: number) {
    const rewards = loadRewards(guildID);
    const index = rewards.findIndex((v) => v.level === atLevel);
    if (index === -1) {
        rewards.push({ level: atLevel, role: roleID });
    } else {
        rewards[index].role = roleID;
    }
    saveRewards(guildID, rewards);
}

function removeRoleReward(guildID: any, atLevel: number) {
    const rewards = loadRewards(guildID);
    const index = rewards.findIndex((v) => v.level === atLevel);
    if (index === -1) return;
    rewards.splice(index, 1);
    saveRewards(guildID, rewards);
}

async function handleRewardMngCommands(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;
    const subGroup = interaction.options.getSubcommandGroup(false);
    if (subGroup !== "leveling") return;
    const subCommand = interaction.options.getSubcommand(false);
    switch (subCommand) {
        case "add-reward": {
            const role = interaction.options.getRole("role", true);
            const level = interaction.options.getNumber("level", true);
            addRoleReward(interaction.guild.id, role.id, level);
            await interaction.reply({
                content: `Set reward ${role.name} to be added on level ${level}`,
                ephemeral: true
            });
            break;
        }
        case "remove-reward": {
            const level = interaction.options.getNumber("level", true);
            removeRoleReward(interaction.guild.id, level);
            await interaction.reply({
                content: "Removed reward",
                ephemeral: true
            });
            break;
        }
    }
}

async function updateMemberRoles(msg: Message<boolean>) {
    const rewards = loadRewards(msg.guild!.id);
    const points = getUserPoints(msg.guild!.id, msg.author.id);
    const level = getUserLevel(points);
    const member = msg.guild!.members.cache.get(msg.author.id);
    if (!member) return;
    const rolesToAdd = rewards.filter((v) => v.level <= level);
    rolesToAdd.forEach((v) => {
        if (!member.roles.cache.has(v.role)) member.roles.add(v.role);
    });
    const rolesToRemove = rewards.filter((v) => v.level > level);
    rolesToRemove.forEach((v) => {
        if (member.roles.cache.has(v.role)) member.roles.remove(v.role);
    });
}

export class LevelingModule implements Module {
    commands: AllCommands = [
        new SlashCommandBuilder().setName("level").setDescription("Get your current level").setDMPermission(false),
        new SlashCommandBuilder().setName("rank").setDescription("Get your current level").setDMPermission(false)
    ];
    selfMemberId: string = "";

    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        if (!interaction.guild) return;
        if (interaction.commandName === "level" || interaction.commandName === "rank") {
            await handleLevelCommand(interaction);
        }

        if (interaction.commandName === "settings") {
            await handleRewardMngCommands(interaction);
        }
    }

    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}

    async onRoleCreate(role: Role): Promise<void> {}

    async onRoleEdit(before: Role, after: Role): Promise<void> {}

    async onRoleDelete(role: Role): Promise<void> {}

    async onChannelCreate(role: Channel): Promise<void> {}

    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}

    async onChannelDelete(role: Channel): Promise<void> {}

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
            await updateMemberRoles(msg);
        }
    }

    async onMessageDelete(msg: Message<boolean>): Promise<void> {}

    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {}

    async onMemberJoin(member: GuildMember): Promise<void> {}

    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}

    async onMemberLeave(member: GuildMember): Promise<void> {}

    async onGuildAdd(guild: Guild): Promise<void> {}

    async onGuildRemove(guild: Guild): Promise<void> {}

    async onGuildEdit(before: Guild, after: Guild): Promise<void> {}

    async onEmojiCreate(emoji: Emoji): Promise<void> {}

    async onEmojiDelete(emoji: Emoji): Promise<void> {}

    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}

    async onStickerCreate(sticker: Sticker): Promise<void> {}

    async onStickerDelete(sticker: Sticker): Promise<void> {}

    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}

    async onReady(client: Client): Promise<void> {}
}
