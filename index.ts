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

dotenv.config();

if (process.env.DEV !== "true" && process.env.SENTRY) {
    console.log("Initializing Sentry...");
    Sentry.init({
        dsn: process.env.SENTRY,
        integrations: [new ProfilingIntegration()],
        tracesSampleRate: 1.0,
        profilesSampleRate: 1.0
    });
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
            restClient.put(Routes.applicationGuildCommands(process.env.CLIENT_ID!, process.env.DEV_GUILD_ID), {
                body: commands
            });
        } else {
            console.log("Registering commands globally...");
            restClient.put(Routes.applicationCommands(process.env.CLIENT_ID!), {
                body: commands
            });
        }
    } catch (error) {
        console.error(error);
    }

    client.user?.setActivity({
        name: "b4",
        type: ActivityType.Playing
    });

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
});

client.on("messageCreate", async (message) => {
    if (!message.guild) return;

    modules.forEach((module) => {
        module.onMessage(message);
    });
});

client.on("interactionCreate", async (interaction) => {
    if (interaction.isButton()) {
        modules.forEach((module) => {
            module.onButtonClick(interaction);
        });
    }

    if (interaction.isChatInputCommand()) {
        modules.forEach((module) => {
            module.onSlashCommand(interaction);
        });
    }
});

client.on("guildMemberAdd", async (member) => {
    modules.forEach((module) => {
        module.onMemberJoin(member);
    });
});

client.on("guildMemberRemove", async (member) => {
    modules.forEach((module) => {
        module.onMemberLeave(member);
    });
});

client.on("guildMemberUpdate", async (before, after) => {
    modules.forEach((module) => {
        module.onMemberEdit(before, after);
    });
});

client.on("messageDelete", async (message) => {
    modules.forEach((module) => {
        module.onMessageDelete(message);
    });
});

client.on("messageUpdate", async (before, after) => {
    modules.forEach((module) => {
        module.onMessageEdit(before, after);
    });
});

client.on("channelCreate", async (channel) => {
    modules.forEach((module) => {
        module.onChannelCreate(channel);
    });
});

client.on("channelDelete", async (channel) => {
    modules.forEach((module) => {
        module.onChannelDelete(channel);
    });
});

client.on("channelUpdate", async (before, after) => {
    modules.forEach((module) => {
        module.onChannelEdit(before, after);
    });
});

client.on("roleCreate", async (role) => {
    modules.forEach((module) => {
        module.onRoleCreate(role);
    });
});

client.on("roleDelete", async (role) => {
    modules.forEach((module) => {
        module.onRoleDelete(role);
    });
});

client.on("roleUpdate", async (before, after) => {
    modules.forEach((module) => {
        module.onRoleEdit(before, after);
    });
});

client.on("guildCreate", async (guild) => {
    modules.forEach((module) => {
        module.onGuildAdd(guild);
    });
});

client.on("guildDelete", async (guild) => {
    modules.forEach((module) => {
        module.onGuildRemove(guild);
    });
});

client.on("guildUpdate", async (before, after) => {
    modules.forEach((module) => {
        module.onGuildEdit(before, after);
    });
});

client.on("emojiCreate", async (emoji) => {
    modules.forEach((module) => {
        module.onEmojiCreate(emoji);
    });
});

client.on("emojiDelete", async (emoji) => {
    modules.forEach((module) => {
        module.onEmojiDelete(emoji);
    });
});

client.on("emojiUpdate", async (before, after) => {
    modules.forEach((module) => {
        module.onEmojiEdit(before, after);
    });
});

client.on("stickerCreate", async (sticker) => {
    modules.forEach((module) => {
        module.onStickerCreate(sticker);
    });
});

client.on("stickerDelete", async (sticker) => {
    modules.forEach((module) => {
        module.onStickerDelete(sticker);
    });
});

client.on("stickerUpdate", async (before, after) => {
    modules.forEach((module) => {
        module.onStickerEdit(before, after);
    });
});

client.on("error", (error) => {
    console.error(error);
});

client.login(process.env.TOKEN);
