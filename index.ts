import { ActivityType, Client, ClientOptions, REST, Routes } from "discord.js";
import { AllCommands, Module } from "./modules/type";
import { Suggestions } from "./modules/suggestions";
import * as dotenv from "dotenv";
import { Logging } from "./modules/logging";
import { SettingsModule } from "./modules/settings";
import { LevelingModule } from "./modules/leveling";
import { WelcomeModule } from "./modules/welcome";
import { GoodbyeModule } from "./modules/goodbye";
import * as Sentry from "@sentry/node";
import { ProfilingIntegration } from "@sentry/profiling-node";
import { ReactionRolesModule } from "./modules/reactionRoles";
import { AntiRaidModule } from "./modules/antiRaid";
import { ModerationModule } from "./modules/moderation";
import { AnalyticsModule } from "./modules/analytics";
import { AntiSpamModule } from "./modules/antiSpam";
import { isServerBlocked, isUserBlocked } from "./utilities/blockList";
import { MediaOnlyChannelModule } from "./modules/mediaOnlyChannels";
import { ChatStreakModule } from "./modules/chatStreak";
import { ChatReviveModule } from "./modules/chatRevive";

dotenv.config();

if (process.env.DEV !== "true" && process.env.SENTRY) {
    console.log("Initializing Sentry...");
    Sentry.init({
        dsn: process.env.SENTRY,
        integrations: [new ProfilingIntegration()],
        tracesSampleRate: 1.0,
        profilesSampleRate: 1.0
    });
} else {
    console.log("Sentry logging is disabled, please use this in development only.");
}

if (!process.env.TOKEN) {
    throw new Error("No token provided");
}
if (!process.env.CLIENT_ID) {
    throw new Error("No client id provided");
}
if (!process.env.SUGGESTION_WEBHOOK_URL) {
    console.warn("No suggestion webhook url provided, suggestions will be discarded");
}

const options: ClientOptions = {
    intents: [
        "AutoModerationConfiguration",
        "AutoModerationExecution",
        "GuildBans",
        "GuildEmojisAndStickers",
        "GuildIntegrations",
        "GuildInvites",
        "GuildMembers",
        "GuildMessageTyping",
        "GuildMessageReactions",
        "GuildMessages",
        "GuildModeration",
        "GuildPresences",
        "GuildScheduledEvents",
        "GuildVoiceStates",
        "GuildWebhooks",
        "Guilds",
        "MessageContent"
    ]
};

const client = new Client(options);
const restClient = new REST().setToken(process.env.TOKEN);
const modules: Module[] = [];

modules.push(new Suggestions());
modules.push(new Logging());
modules.push(new SettingsModule());
modules.push(new LevelingModule());
modules.push(new WelcomeModule());
modules.push(new GoodbyeModule());
modules.push(new ReactionRolesModule());
modules.push(new AntiRaidModule());
modules.push(new ModerationModule());
modules.push(new AnalyticsModule());
modules.push(new AntiSpamModule());
modules.push(new MediaOnlyChannelModule());
modules.push(new ChatStreakModule());
modules.push(new ChatReviveModule());

client.on("ready", async () => {
    console.log("I am ready!");
    modules.forEach((module) => {
        module.selfMemberId = client.user?.id ?? "";
    });
    try {
        let commands: AllCommands = [];
        modules.forEach((module) => {
            commands = [...commands, ...module.commands];
        });

        if (process.env.DEV === "true" && process.env.DEV_GUILD_ID) {
            console.log("Registering commands in dev guild...");
            await restClient.put(Routes.applicationGuildCommands(process.env.CLIENT_ID!, process.env.DEV_GUILD_ID), {
                body: commands
            });
        } else {
            console.log("Registering commands globally...");
            await restClient.put(Routes.applicationCommands(process.env.CLIENT_ID!), {
                body: commands
            });
        }
    } catch (error) {
        console.error(error);
    }

    console.log(`Loaded with ${client.guilds.cache.size} guilds...`);
    for (const guild of client.guilds.cache.values()) {
        console.log(`\tGuild ${guild.name} (${guild.id})`);
        const channels = guild.channels.cache;
        console.log(
            `\t\t${channels.size} channels (${channels.filter((channel) => channel.isTextBased()).size} text, ${
                channels.filter((channel) => channel.isVoiceBased()).size
            } voice)`
        );

        console.log(`\t\t${guild.members.cache.size} members...`);
    }

    client.user?.setActivity({
        name: `v1.0 | ${client.guilds.cache.size} guilds`,
        type: ActivityType.Playing
    });

    setInterval(() => {
        client.user?.setActivity({
            name: `v1.0 | ${client.guilds.cache.size} guilds`,
            type: ActivityType.Playing
        });
    }, 300 * 1000);

    console.log("Starting tick tasks...");
    modules.forEach(x => {
        x.onReady(client);
        setInterval(x.onTick, 5 * 1000);
    })
});

client.on("messageCreate", async (message) => {
    if (!message.guild) return;

    if (isServerBlocked(message.guild.id) || isUserBlocked(message.author.id)) return;

    modules.forEach((module) => {
        module.onMessage(message);
    });
});

client.on("interactionCreate", async (interaction) => {
    if (interaction.isButton()) {
        if (!interaction.guild) return;
        if (isServerBlocked(interaction.guild.id) || isUserBlocked(interaction.user.id)) {
            await interaction.reply({
                content:
                    "Internal Server Error: Database reported server or user is blocked from using this bot. No further information...",
                ephemeral: true
            });
            return;
        }
        modules.forEach((module) => {
            module.onButtonClick(interaction);
        });
    }

    if (interaction.isChatInputCommand()) {
        if (!interaction.guild) return;
        if (isServerBlocked(interaction.guild.id) || isUserBlocked(interaction.user.id)) {
            await interaction.reply({
                content:
                    "Internal Server Error: Database reported server or user is blocked from using this bot. No further information...",
                ephemeral: true
            });
            return;
        }
        modules.forEach((module) => {
            module.onSlashCommand(interaction);
        });
    }
});

client.on("guildMemberAdd", async (member) => {
    if (!member.guild) return;
    if (isServerBlocked(member.guild.id) || isUserBlocked(member.user.id)) return;
    modules.forEach((module) => {
        module.onMemberJoin(member);
    });
});

client.on("guildMemberRemove", async (member) => {
    if (!member.guild) return;
    if (isServerBlocked(member.guild.id) || isUserBlocked(member.user.id)) return;
    modules.forEach((module) => {
        module.onMemberLeave(member);
    });
});

client.on("guildMemberUpdate", async (before, after) => {
    if (!after.guild) return;
    if (isServerBlocked(after.guild.id) || isUserBlocked(after.user.id)) return;
    modules.forEach((module) => {
        module.onMemberEdit(before, after);
    });
});

client.on("messageDelete", async (message) => {
    if (!message.guild) return;
    if (isServerBlocked(message.guild.id)) return;
    modules.forEach((module) => {
        module.onMessageDelete(message);
    });
});

client.on("messageUpdate", async (before, after) => {
    if (!after.guild) return;
    if (isServerBlocked(after.guild.id)) return;
    modules.forEach((module) => {
        module.onMessageEdit(before, after);
    });
});

client.on("channelCreate", async (channel) => {
    if (!channel.guild) return;
    if (isServerBlocked(channel.guild.id)) return;
    modules.forEach((module) => {
        module.onChannelCreate(channel);
    });
});

client.on("channelDelete", async (channel) => {
    if (channel.isDMBased()) return;
    if (!channel.guild) return;
    if (isServerBlocked(channel.guild.id)) return;
    modules.forEach((module) => {
        module.onChannelDelete(channel);
    });
});

client.on("channelUpdate", async (before, after) => {
    if (after.isDMBased()) return;
    if (!after.guild) return;
    if (isServerBlocked(after.guild.id)) return;
    modules.forEach((module) => {
        module.onChannelEdit(before, after);
    });
});

client.on("roleCreate", async (role) => {
    if (!role.guild) return;
    if (isServerBlocked(role.guild.id)) return;
    modules.forEach((module) => {
        module.onRoleCreate(role);
    });
});

client.on("roleDelete", async (role) => {
    if (!role.guild) return;
    if (isServerBlocked(role.guild.id)) return;
    modules.forEach((module) => {
        module.onRoleDelete(role);
    });
});

client.on("roleUpdate", async (before, after) => {
    if (!after.guild) return;
    if (isServerBlocked(after.guild.id)) return;
    modules.forEach((module) => {
        module.onRoleEdit(before, after);
    });
});

client.on("guildCreate", async (guild) => {
    if (isServerBlocked(guild.id)) return;
    modules.forEach((module) => {
        module.onGuildAdd(guild);
    });
});

client.on("guildDelete", async (guild) => {
    if (isServerBlocked(guild.id)) return;
    modules.forEach((module) => {
        module.onGuildRemove(guild);
    });
});

client.on("guildUpdate", async (before, after) => {
    if (isServerBlocked(after.id)) return;
    modules.forEach((module) => {
        module.onGuildEdit(before, after);
    });
});

client.on("emojiCreate", async (emoji) => {
    if (!emoji.guild) return;
    if (isServerBlocked(emoji.guild.id)) return;
    modules.forEach((module) => {
        module.onEmojiCreate(emoji);
    });
});

client.on("emojiDelete", async (emoji) => {
    if (!emoji.guild) return;
    if (isServerBlocked(emoji.guild.id)) return;
    modules.forEach((module) => {
        module.onEmojiDelete(emoji);
    });
});

client.on("emojiUpdate", async (before, after) => {
    if (!after.guild) return;
    if (isServerBlocked(after.guild.id)) return;
    modules.forEach((module) => {
        module.onEmojiEdit(before, after);
    });
});

client.on("stickerCreate", async (sticker) => {
    if (!sticker.guild) return;
    if (isServerBlocked(sticker.guild.id)) return;
    modules.forEach((module) => {
        module.onStickerCreate(sticker);
    });
});

client.on("stickerDelete", async (sticker) => {
    if (!sticker.guild) return;
    if (isServerBlocked(sticker.guild.id)) return;
    modules.forEach((module) => {
        module.onStickerDelete(sticker);
    });
});

client.on("stickerUpdate", async (before, after) => {
    if (!after.guild) return;
    if (isServerBlocked(after.guild.id)) return;
    modules.forEach((module) => {
        module.onStickerEdit(before, after);
    });
});

client.on("error", (error) => {
    console.error(error);
});

client.login(process.env.TOKEN);
