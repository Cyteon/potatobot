import { SlashCommandBuilder } from "@discordjs/builders";

const data = new SlashCommandBuilder()
  .setName("github")
  .setDescription("Returns data from GitHub.")
  .addSubcommand((subcommand) =>
    subcommand
    .setName("user")
    .setDescription("Gets a GitHub profile via their username.")
    .addStringOption((input) =>
        input
          .setName("username")
          .setDescription("...")
          .setRequired(true)
      )
  )
  .addSubcommand((subcommand) =>
    subcommand
      .setName("repo")
      .setDescription("Searches for the specified GitHub repo.")
      .addStringOption((input) =>
        input
          .setName("owner")
          .setDescription("...")
          .setRequired(true)
      )
      .addStringOption((input) =>
        input
          .setName("repo")
          .setDescription("...")
          .setRequired(true)
      )
  );

const execute = async function (interaction) {
    const { options } = interaction;
    const subCommand = options.getSubcommand();

    if (subCommand === "user") {
        const user = options.getString("username")
        const response = await fetch(`https://api.github.com/users/${user}`);
    } else if (subCommand === "repo") {
        
    }
};

export default { data, execute };
