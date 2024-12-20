import { SlashCommandBuilder, EmbedBuilder, PermissionsBitField } from 'discord.js';

// this command requires "Manage messages" perms to see

export default {
    data: new SlashCommandBuilder()
     .setName('giveaway')
     .setDescription('create a giveaway')
     .setDefaultMemberPermissions(PermissionsBitField.Flags.ManageMessages)
     .addSubcommand(subcommand =>
        subcommand
          .setName('start')
          .setDescription('start a giveaway')
          .addStringOption(option =>
            option
              .setName('prize')
              .setDescription('the prize to win')
              .setRequired(true)
          )
          .addIntegerOption(option =>
            option
              .setName('duration')
              .setDescription('the duration in hours')
              .setRequired(true)
          )
          .addIntegerOption(option =>
            option
              .setName('winners')
              .setDescription('amount of winners')
              .setRequired(true)
          )
     )
     .addSubcommand(subcommand =>
        subcommand
          .setName('reroll')
          .setDescription('reroll the giveaway')
          .addStringOption(option =>
            option
              .setName('message_id')
              .setDescription('the message id of the giveaway')
              .setRequired(true)
          )
     )
    .addSubcommand(subcommand =>
       subcommand
         .setName('end')
         .setDescription('end the giveaway')
         .addStringOption(option =>
           option
             .setName('messageid')
             .setDescription('the message id of the giveaway')
             .setRequired(true)
         )
    ),
    async execute(interaction) {
        const subcommand = interaction.options.getSubcommand();

        if (subcommand === 'start') {
            const prize = interaction.options.getString('prize');
            const duration = interaction.options.getInteger('duration');
            const winnersCount = interaction.options.getInteger('winners');
            
            if (duration < 1) {
              return interaction.reply({
                  content: 'The duration must be at least 1 hour.',
                  ephemeral: true,
              });
          }

            if (winnersCount < 1) {
              return interaction.reply({
                  content: 'There must be more than 0 winners.',
                  ephemeral: true,
              });
          }
          
            const embed = new EmbedBuilder()
              .setTitle('🎉Giveaway!')
              .setDescription(`**Prize:** ${prize}\n**React with 🎉 to enter!**\n**Winners:** ${winnersCount}\n**Ends in:** ${duration} hours`)
              .setColor('#00FFFF')
              .setTimestamp(Date.now() + duration * 60 * 60 * 1000);

              const giveawayMessage = await interaction.reply({ embeds: [embed], fetchReply: true});
              giveawayMessage.react('🎉');

              setTimeout(async () => {
                const users = await giveawayMessage.reactions.resolve('🎉').users.fetch();
                const validUsers = users.filter(user => !user.bot);
                const winnersCount = interaction.options.getInteger('winners');
                const duration = interaction.options.getInteger('duration');

                if (validUsers.size < winnersCount) {
                    return interaction.channel.send(`Not enough partipants for the giveaway **${prize}**.`);
                }

                const winners = validUsers.random(winnersCount).map(user => user.toString());
                interaction.channel.send(`🎉 Congrats ${winners.join()}! You won **${prize}**!`);
              }, duration * 60 * 60 * 1000);
        }

        if (subcommand === 'reroll') {
            const messageId = interaction.options.getString('message_id');

            try {
               const message = await interaction.channel.messages.fetch(messageId);
               const users = await message.reactions.resolve('🎉').users.fetch();
               const validUsers = users.filter(user => !user.bot);

               if (validUsers.size === 0) {
                return interaction.reply('No valid participants to reroll.');
               }

               const winner = validUsers.random();
               interaction.reply(`🎉 The new winner is ${winner.toString()}!`);
            } catch (error) {
                interaction.reply('Could not fetch the giveaway message. Please check the message id.');
            }
        }

        if (subcommand === 'end') {
            const messageId = interaction.options.getString('messageid');

            try {
               const message = await interaction.channel.messages.fetch(messageId);
               const users = await message.reactions.resolve('🎉').users.fetch();
               const validUsers = users.filter(user => !user.bot);
               const winners = validUsers.random().toString();

               if (validUsers.size === 0) {
                return interaction.reply('No participants are in this giveaway.');
               }

               interaction.reply(`🎉 The giveaway has ended! The winner is ${winners}`);
            } catch (error) {
                interaction.reply('Could not fetch the giveaway message. Please check the message ID.');
            }
        }
    },
};
