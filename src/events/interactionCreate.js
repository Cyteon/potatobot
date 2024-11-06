import GlobalUser from "../lib/models/GlobalUser.js";

export default {
  name: "interactionCreate",
  async execute(interaction, client) {
    if (!interaction.isCommand()) return;

    const command = client.commands.get(interaction.commandName);

    if (!command) return;

    let user = await GlobalUser.findOne({ id: interaction.user.id });

    console.log(user);

    if (!user) {
      user = await GlobalUser.create({
        id: interaction.user.id,
      });
    }

    if (user.blacklisted) {
      return await interaction.reply({
        content: `:no_entry: You are blacklisted from using commands! Reason: ${user.blacklist_reason}`,
        ephemeral: true,
      });
    }

    try {
      await command.execute(interaction, client);
    } catch (error) {
      console.log(error);
      try {
        await interaction.reply({
          content: "There was an error while executing this command!",
          ephemeral: true,
        });
      } catch (error) {
        console.log(
          "Error while handling error in interactionCreate event: ",
          error,
        );
      }
    }
  },
};
