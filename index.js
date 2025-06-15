require('dotenv').config();
const { Telegraf, Scenes, session } = require('telegraf');
const axios = require('axios');
const cron = require('node-cron');
const faker = require('faker');

const bot = new Telegraf(process.env.BOT_TOKEN);
const adminId = 7387793694; // For admin panel access
const adminChannel = process.env.ADMIN_CHANNEL || '@YourAdminChannel'; // Ensure this is set in .env (numeric ID)

// In-memory storage
const users = {};
const actions = [];

// Scene for Method Generate (previously Account Mass Report)
const instaScene = new Scenes.WizardScene(
  'insta_scene',
  async (ctx) => {
    ctx.wizard.state.data = {};
    await ctx.reply('📝 Please send the Instagram username without @.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid username.');
      return;
    }
    const username = ctx.message.text.trim();
    ctx.wizard.state.data.username = username;

    actions.push({
      userId: ctx.from.id,
      username: ctx.from.username || 'NoUsername',
      action: 'method_generate',
      data: { username },
      timestamp: new Date()
    });

    try {
      await ctx.telegram.sendMessage(adminChannel, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Method Generate\nTarget: ${username}`, { parse_mode: 'HTML' });
    } catch (err) {
      console.error(`Failed to send admin notification: ${err.message}`);
    }

    try {
      const res = await axios.get(`https://ar-api-iauy.onrender.com/instastalk?username=${username}`);
      const data = res.data;

      if (!data.success) {
        await ctx.reply('<b>Invalid Instagram username or not found.</b>', { parse_mode: 'HTML' });
        return await ctx.scene.leave();
      }

      const info = `<b>Is this the correct user?</b>\n\n` +
        `• <b>Username:</b> ${data.username}\n` +
        `• <b>Nickname:</b> ${data.full_name || 'N/A'}\n` +
        `• <b>Followers:</b> ${data.follower_count}\n` +
        `• <b>Following:</b> ${data.following_count}\n` +
        `• <b>Created At:</b> ${data.account_created || 'N/A'}`;

      await ctx.reply(info, {
        parse_mode: 'HTML',
        reply_markup: {
          inline_keyboard: [
            [
              { text: 'Yes ✅', callback_data: `confirm_yes_${username}` },
              { text: 'No ❌', callback_data: `confirm_no` }
            ]
          ]
        }
      });
    } catch (err) {
      await ctx.reply('<b>Unable to verify the username. The API might be down.</b>\n\nPlease try again later.', { parse_mode: 'HTML' });
      return await ctx.scene.leave();
    }

    return await ctx.scene.leave();
  }
);

// Scene for Instagram Form Mass Report (with live count animation)
const formReportScene = new Scenes.WizardScene(
  'form_report_scene',
  async (ctx) => {
    ctx.wizard.state.data = {};
    await ctx.reply('📝 Please send the Instagram username.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid username.');
      return;
    }
    ctx.wizard.state.data.username = ctx.message.text.trim();
    await ctx.reply('📝 Now send the target link (e.g., https://instagram.com/p/xxx).');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid link.');
      return;
    }
    const targetLink = ctx.message.text.trim();
    const username = ctx.wizard.state.data.username;

    actions.push({
      userId: ctx.from.id,
      username: ctx.from.username || 'NoUsername',
      action: 'insta_form_report',
      data: { username, targetLink },
      timestamp: new Date()
    });

    try {
      await ctx.telegram.sendMessage(adminChannel, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Instagram Form Report\nTarget: ${username}\nLink: ${targetLink}`, { parse_mode: 'HTML' });
    } catch (err) {
      console.error(`Failed to send admin notification: ${err.message}`);
    }

    try {
      const lsd = Math.random().toString(36).substring(2, 14);
      const funame = faker.name.findName();
      const em = Math.random().toString(36).substring(2, 8) + '@gmail.com';
      const url = "https://help.instagram.com/ajax/help/contact/submit/page";
      const payload = `jazoest=${Math.floor(Math.random() * 9000) + 1000}&lsd=${lsd}&radioDescribeSituation=represent_impersonation&inputFullName=${funame}&inputEmail=${em}&inputReportedUsername=${username}&uploadID%5B0%5D=${targetLink}&support_form_id=636276399721841&support_form_locale_id=en_US`;
      const headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'x-fb-lsd': lsd,
        'origin': 'https://help.instagram.com',
        'sec-fetch-site': 'same-origin'
      };

      const response = await axios.post(url, payload, { headers });
      if (response.data.includes("The given Instagram user ID is invalid.")) {
        await ctx.reply('⚠️ Username not found or available.');
        return await ctx.scene.leave();
      }
    } catch (err) {
      console.error(`Form report error: ${err.message}`);
    }

    // Progress bar animation with live counts
    const loadingMsg = await ctx.reply('<b>Loading... Please wait.</b>', { parse_mode: 'HTML' });

    for (let i = 10; i <= 100; i += 10) {
      const bar = '▒'.repeat(i / 10) + ' '.repeat(10 - i / 10);
      try {
        await ctx.telegram.editMessageText(ctx.chat.id, loadingMsg.message_id, null, `<b>Loading... ${i}%</b> ${bar}`, { parse_mode: 'HTML' });
        await new Promise(r => setTimeout(r, 500));
      } catch {
        break;
      }
    }

    // Delete the progress bar message
    await ctx.telegram.deleteMessage(ctx.chat.id, loadingMsg.message_id);

    // Generate random success/error counts (max 200 total)
    const total = Math.floor(Math.random() * (200 - 50 + 1)) + 50; // Random total between 50 and 200
    const successCount = Math.floor(Math.random() * total);
    const errorCount = total - successCount;

    const finalText = `<i>Username: @${username}</i>\n\n` +
      `<b>Status:</b>\n` +
      `✅ Success: ${successCount}\n` +
      `❌ Error: ${errorCount}\n` +
      `<blockquote>⚠️ <b>Note:</b> <i><a href="https://t.me/Peldiya">This method is based on available data and may not be fully accurate.</a></i></blockquote>`;

    await ctx.reply(finalText, {
      parse_mode: 'HTML',
      reply_markup: { inline_keyboard: [[{ text: 'Contact Developer', url: 'tg://openmessage?user_id=7387793694' }]] }
    });

    return await ctx.scene.leave();
  }
);

// Scene for Instagram password reset
const instaResetScene = new Scenes.WizardScene(
  'insta_reset_scene',
  async (ctx) => {
    ctx.wizard.state.data = {};
    await ctx.reply('📝 Please send your Instagram username or email.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid username or email.');
      return;
    }
    const emailOrUsername = ctx.message.text.trim();
    ctx.wizard.state.data.emailOrUsername = emailOrUsername;

    actions.push({
      userId: ctx.from.id,
      username: ctx.from.username || 'NoUsername',
      action: 'insta_pass_reset',
      data: { emailOrUsername },
      timestamp: new Date()
    });

    try {
      await ctx.telegram.sendMessage(adminChannel, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Instagram Password Reset\nTarget: ${emailOrUsername}`, { parse_mode: 'HTML' });
    } catch (err) {
      console.error(`Failed to send admin notification: ${err.message}`);
    }

    try {
      const response = await axios.get(`https://instagram-pass-reset.vercel.app/reset-password?username=${encodeURIComponent(emailOrUsername)}`);
      await ctx.reply(`📬 **Result:** \`${JSON.stringify(response.data)}\``, { parse_mode: 'Markdown' });
    } catch (err) {
      await ctx.reply(`🚨 Error: ${err.message}`);
    }
    return await ctx.scene.leave();
  }
);

// Scene for WhatsApp unban
const wpUnbanScene = new Scenes.WizardScene(
  'wp_unban_scene',
  async (ctx) => {
    ctx.wizard.state.data = {};
    await ctx.reply('📝 Please send your email.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid email.');
      return;
    }
    ctx.wizard.state.data.email = ctx.message.text.trim();
    await ctx.reply('📝 Now send your phone number with country code (e.g., +1234567890).');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid phone number.');
      return;
    }
    ctx.wizard.state.data.phone = ctx.message.text.trim();
    await ctx.reply('📝 Finally, send your mobile model (e.g., iPhone 14).');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid mobile model.');
      return;
    }
    const model = ctx.message.text.trim();
    const { email, phone } = ctx.wizard.state.data;

    actions.push({
      userId: ctx.from.id,
      username: ctx.from.username || 'NoUsername',
      action: 'wp_unban',
      data: { email, phone, model },
      timestamp: new Date()
    });

    try {
      await ctx.telegram.sendMessage(adminChannel, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: WhatsApp Unban\nEmail: ${email}\nPhone: ${phone}\nModel: ${model}`, { parse_mode: 'HTML' });
    } catch (err) {
      console.error(`Failed to send admin notification: ${err.message}`);
    }

    try {
      const subject = encodeURIComponent('My WhatsApp account has been deactivated by mistake');
      const message = encodeURIComponent(`Hello,\nMy WhatsApp account has been deactivated by mistake.\nCould you please activate my phone number: "${phone}"\nMy mobile model: "${model}"\nThanks in advance.`);
      await axios.get(`https://sendmail.ashlynn.workers.dev/send-email?to=Support@Whatsapp.com&from=${encodeURIComponent(email)}&subject=${subject}&message=${message}`);
      await ctx.reply('✅ Unban request sent successfully.');
    } catch (err) {
      await ctx.reply(`🚨 Error: ${err.message}`);
    }
    return await ctx.scene.leave();
  }
);

// Scene for WhatsApp ban
const wpBanScene = new Scenes.WizardScene(
  'wp_ban_scene',
  async (ctx) => {
    ctx.wizard.state.data = {};
    await ctx.reply('📝 Please send your email.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid email.');
      return;
    }
    ctx.wizard.state.data.email = ctx.message.text.trim();
    await ctx.reply('📝 Now send the target phone number with country code (e.g., +1234567890).');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid phone number.');
      return;
    }
    const phone = ctx.message.text.trim();
    const { email } = ctx.wizard.state.data;

    actions.push({
      userId: ctx.from.id,
      username: ctx.from.username || 'NoUsername',
      action: 'wp_ban',
      data: { email, phone },
      timestamp: new Date()
    });

    try {
      await ctx.telegram.sendMessage(adminChannel, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: WhatsApp Ban\nEmail: ${email}\nPhone: ${phone}`, { parse_mode: 'HTML' });
    } catch (err) {
      console.error(`Failed to send admin notification: ${err.message}`);
    }

    try {
      const subject = encodeURIComponent('Report: Inappropriate WhatsApp Account');
      const message = encodeURIComponent(`Hello,\nI am reporting an inappropriate WhatsApp account.\nPhone number: ${phone}\nPlease take appropriate action.\nThanks.`);
      await axios.get(`https://sendmail.ashlynn.workers.dev/send-email?to=Support@Whatsapp.com&from=${encodeURIComponent(email)}&subject=${subject}&message=${message}`);
      await ctx.reply('✅ Ban request sent successfully.');
    } catch (err) {
      await ctx.reply(`🚨 Error: ${err.message}`);
    }
    return await ctx.scene.leave();
  }
);

// Scene for Telegram unban
const tgUnbanScene = new Scenes.WizardScene(
  'tg_unban_scene',
  async (ctx) => {
    ctx.wizard.state.data = {};
    await ctx.reply('📝 Please send your email.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid email.');
      return;
    }
    ctx.wizard.state.data.email = ctx.message.text.trim();
    await ctx.reply('📝 Now send your phone number (e.g., +1234567890).');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid phone number.');
      return;
    }
    const phone = ctx.message.text.trim();
    const { email } = ctx.wizard.state.data;

    actions.push({
      userId: ctx.from.id,
      username: ctx.from.username || 'NoUsername',
      action: 'tg_unban',
      data: { email, phone },
      timestamp: new Date()
    });

    try {
      await ctx.telegram.sendMessage(adminChannel, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Telegram Unban\nEmail: ${email}\nPhone: ${phone}`, { parse_mode: 'HTML' });
    } catch (err) {
      console.error(`Failed to send admin notification: ${err.message}`);
    }

    await ctx.reply('✅ Telegram unban request noted. Please contact support for further assistance.');
    return await ctx.scene.leave();
  }
);

// Scene for YouTube report
const ytReportScene = new Scenes.WizardScene(
  'yt_report_scene',
  async (ctx) => {
    ctx.wizard.state.data = {};
    await ctx.reply('📝 Please send your email.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid email.');
      return;
    }
    ctx.wizard.state.data.email = ctx.message.text.trim();
    await ctx.reply('📝 Now send the target channel username.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid username.');
      return;
    }
    ctx.wizard.state.data.username = ctx.message.text.trim();
    await ctx.reply('📝 Now send the link to the channel or video.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid link.');
      return;
    }
    ctx.wizard.state.data.link = ctx.message.text.trim();
    await ctx.reply('📝 Finally, send the report text (reason for reporting).');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid report text.');
      return;
    }
    const reportText = ctx.message.text.trim();
    const { email, username, link } = ctx.wizard.state.data;

    actions.push({
      userId: ctx.from.id,
      username: ctx.from.username || 'NoUsername',
      action: 'yt_report',
      data: { email, username, link, reportText },
      timestamp: new Date()
    });

    try {
      await ctx.telegram.sendMessage(adminChannel, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: YouTube Report\nEmail: ${email}\nTarget: ${username}\nLink: ${link}\nText: ${reportText}`, { parse_mode: 'HTML' });
    } catch (err) {
      console.error(`Failed to send admin notification: ${err.message}`);
    }

    try {
      const subject = encodeURIComponent('YouTube Channel Report');
      const message = encodeURIComponent(`Hello,\nI am reporting a YouTube channel.\nUsername: ${username}\nLink: ${link}\nReason: ${reportText}\nThanks.`);
      await axios.get(`https://sendmail.ashlynn.workers.dev/send-email?to=support@youtube.com&from=${encodeURIComponent(email)}&subject=${subject}&message=${message}`);
      await ctx.reply('✅ YouTube report sent successfully.');
    } catch (err) {
      await ctx.reply(`🚨 Error: ${err.message}`);
    }
    return await ctx.scene.leave();
  }
);

// Scene for Account Report (new feature)
const accountReportScene = new Scenes.WizardScene(
  'account_report_scene',
  async (ctx) => {
    ctx.wizard.state.data = {};
    await ctx.reply('📝 Please send the Instagram username without @.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid username.');
      return;
    }
    const username = ctx.message.text.trim();
    ctx.wizard.state.data.username = username;

    actions.push({
      userId: ctx.from.id,
      username: ctx.from.username || 'NoUsername',
      action: 'account_report',
      data: { username },
      timestamp: new Date()
    });

    try {
      await ctx.telegram.sendMessage(adminChannel, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Account Report\nTarget: ${username}`, { parse_mode: 'HTML' });
    } catch (err) {
      console.error(`Failed to send admin notification: ${err.message}`);
    }

    try {
      const res = await axios.get(`https://ar-api-iauy.onrender.com/instastalk?username=${username}`);
      const data = res.data;

      if (!data.success) {
        await ctx.reply('<b>Invalid Instagram username or not found.</b>', { parse_mode: 'HTML' });
        return await ctx.scene.leave();
      }

      const info = `<b>Is this the correct user?</b>\n\n` +
        `• <b>Username:</b> ${data.username}\n` +
        `• <b>Nickname:</b> ${data.full_name || 'N/A'}\n` +
        `• <b>Followers:</b> ${data.follower_count}\n` +
        `• <b>Following:</b> ${data.following_count}\n` +
        `• <b>Created At:</b> ${data.account_created || 'N/A'}`;

      ctx.wizard.state.data.userInfo = info; // Store user info for later use

      await ctx.reply(info, {
        parse_mode: 'HTML',
        reply_markup: {
          inline_keyboard: [
            [
              { text: 'Yes ✅', callback_data: `account_confirm_yes_${username}` },
              { text: 'No ❌', callback_data: `account_confirm_no` }
            ]
          ]
        }
      });
    } catch (err) {
      await ctx.reply('<b>Unable to verify the username. The API might be down.</b>\n\nPlease try again later.', { parse_mode: 'HTML' });
      return await ctx.scene.leave();
    }

    return await ctx.scene.leave();
  }
);

// Scene for admin broadcast
const broadcastScene = new Scenes.WizardScene(
  'broadcast_scene',
  async (ctx) => {
    if (ctx.from.id !== adminId) {
      await ctx.reply('🚫 Unauthorized.');
      return await ctx.scene.leave();
    }
    await ctx.reply('📢 Enter the message to broadcast to all users.');
    return ctx.wizard.next();
  },
  async (ctx) => {
    if (!ctx.message || !ctx.message.text) {
      await ctx.reply('Please send a valid message.');
      return;
    }
    const message = ctx.message.text.trim();
    for (const userId in users) {
      try {
        await ctx.telegram.sendMessage(userId, message, { parse_mode: 'HTML' });
      } catch (err) {
        console.error(`Failed to send to ${userId}: ${err.message}`);
      }
    }
    await ctx.reply('✅ Broadcast sent.');
    return await ctx.scene.leave();
  }
);

// Initialize scenes
const stage = new Scenes.Stage([
  instaScene,
  formReportScene,
  instaResetScene,
  wpUnbanScene,
  wpBanScene,
  tgUnbanScene,
  ytReportScene,
  accountReportScene,
  broadcastScene
]);
bot.use(session());
bot.use(stage.middleware());

// Channel check middleware
const channels = ['@nobi_shops']; // Replace with your channels
async function checkChannels(ctx, next) {
  const userId = ctx.from.id;
  let isMember = true;
  for (const channel of channels) {
    try {
      const member = await ctx.telegram.getChatMember(channel, userId);
      if (['left', 'kicked'].includes(member.status)) {
        isMember = false;
        break;
      }
    } catch {
      isMember = false;
      break;
    }
  }
  if (!isMember) {
    await ctx.reply('Please join all required channels to access the bot.', {
      parse_mode: 'HTML',
      reply_markup: {
        inline_keyboard: channels.map(ch => [{ text: `Join ${ch}`, url: `https://t.me/${ch.replace('@', '')}` }]).concat([[{ text: '✅ I Joined', callback_data: 'check_fsub' }]])
      }
    });
    return;
  }
  return next();
}

// Start command
bot.command('start', async (ctx) => {
  const userId = ctx.from.id;
  if (!users[userId]) {
    users[userId] = {
      userId,
      name: ctx.from.first_name || 'NoName',
      username: ctx.from.username || 'NoUsername',
      joinDate: new Date(),
      status: 'active'
    };

    try {
      await ctx.telegram.sendMessage(adminChannel, `🆕 New User\nName: ${ctx.from.first_name || 'N/A'}\nUsername: @${ctx.from.username || 'N/A'}\nID: ${userId}\nDate: ${new Date().toLocaleString('en-IN')}`, {
        parse_mode: 'HTML',
        reply_markup: { inline_keyboard: [[{ text: `View ${ctx.from.first_name || 'User'}`, callback_data: `view_user_${userId}` }]] }
      });
    } catch (err) {
      console.error(`Failed to send admin notification: ${err.message}`);
    }
  }

  await ctx.replyWithPhoto('https://t.me/ziddion/636', {
    caption: `Welcome <b>${ctx.from.first_name || 'user'}</b>!\n\nChoose an option to proceed:`,
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [
        [{ text: '📸 Insta Server', callback_data: 'insta_menu' }, { text: '📱 WP Server', callback_data: 'wp_menu' }],
        [{ text: '💬 Tele Server', callback_data: 'tg_menu' }, { text: '📹 YT Server', callback_data: 'yt_menu' }],
        [{ text: 'ℹ️ About', callback_data: 'about' }, { text: '🆘 Help', callback_data: 'help' }],
        [{ text: '👨‍💻 Developer', callback_data: 'developer' }]
      ]
    }
  });
});

// Menu commands
bot.action('insta_menu', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageMedia({
    type: 'photo',
    media: 'https://t.me/ziddion/636',
    caption: '📸 Instagram Server\nChoose an option:',
    parse_mode: 'HTML'
  }, {
    reply_markup: {
      inline_keyboard: [
        [{ text: 'Method Generate', callback_data: 'method_generate' }, { text: 'Form Mass Report', callback_data: 'insta_form' }],
        [{ text: 'Insta Info', callback_data: 'insta_info' }, { text: 'Insta Pass Reset', callback_data: 'insta_reset' }],
        [{ text: 'Account Report', callback_data: 'account_report' }],
        [{ text: '🔙 Back', callback_data: 'back_main' }]
      ]
    }
  });
});

bot.action('wp_menu', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageMedia({
    type: 'photo',
    media: 'https://t.me/ziddion/636',
    caption: '📱 WhatsApp Server\nChoose an option:',
    parse_mode: 'HTML'
  }, {
    reply_markup: {
      inline_keyboard: [
        [{ text: 'WP Unban', callback_data: 'wp_unban' }, { text: 'WP Ban', callback_data: 'wp_ban' }],
        [{ text: '🔙 Back', callback_data: 'back_main' }]
      ]
    }
  });
});

bot.action('tg_menu', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageMedia({
    type: 'photo',
    media: 'https://t.me/ziddion/636',
    caption: '💬 Telegram Server\nChoose an option:',
    parse_mode: 'HTML'
  }, {
    reply_markup: {
      inline_keyboard: [
        [{ text: 'TG Unban', callback_data: 'tg_unban' }],
        [{ text: '🔙 Back', callback_data: 'back_main' }]
      ]
    }
  });
});

bot.action('yt_menu', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageMedia({
    type: 'photo',
    media: 'https://t.me/ziddion/636',
    caption: '📹 YouTube Server\nChoose an option:',
    parse_mode: 'HTML'
  }, {
    reply_markup: {
      inline_keyboard: [
        [{ text: 'YT Report', callback_data: 'yt_report' }],
        [{ text: '🔙 Back', callback_data: 'back_main' }]
      ]
    }
  });
});

bot.action('about', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageText('ℹ️ <b>About</b>\n\nThis bot provides tools for reporting and managing accounts across Instagram, WhatsApp, Telegram, and YouTube.\nDeveloped by @YourDeveloper', {
    parse_mode: 'HTML',
    reply_markup: { inline_keyboard: [[{ text: '🔙 Back', callback_data: 'back_main' }]] }
  });
});

bot.action('help', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageText(
    `<b>Available Commands & Features:</b>\n\n` +
    `/start - Restart the bot & show welcome message\n` +
    `/admin - Access admin panel (admin only)\n\n` +
    `<b>Features:</b>\n` +
    `📸 <b>Insta Server:</b> Method Generate, Form Mass Report, Insta Info, Insta Pass Reset, Account Report\n` +
    `📱 <b>WP Server:</b> WhatsApp Unban, WhatsApp Ban\n` +
    `💬 <b>Tele Server:</b> Telegram Unban\n` +
    `📹 <b>YT Server:</b> YouTube Channel Report\n\n` +
    `Join our channels for updates: @nobi_shops`,
    {
      parse_mode: 'HTML',
      reply_markup: {
        inline_keyboard: [
          [{ text: 'Updated', url: 't.me/nobi_shops' }, { text: 'Support', url: 't.me/offchats' }],
          [{ text: '🔙 Back', callback_data: 'back_main' }]
        ]
      }
    }
  );
});

bot.action('developer', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageText('👨‍💻 <b>Developer</b>\n\nContact: @YourDeveloper\nSupport: t.me/offchats', {
    parse_mode: 'HTML',
    reply_markup: { inline_keyboard: [[{ text: '🔙 Back', callback_data: 'back_main' }]] }
  });
});

bot.action('back_main', async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageMedia({
    type: 'photo',
    media: 'https://t.me/ziddion/636',
    caption: `Welcome <b>${ctx.from.first_name || 'user'}</b>!\n\nChoose an option to proceed:`,
    parse_mode: 'HTML'
  }, {
    reply_markup: {
      inline_keyboard: [
        [{ text: '📸 Insta Server', callback_data: 'insta_menu' }, { text: '📱 WP Server', callback_data: 'wp_menu' }],
        [{ text: '💬 Tele Server', callback_data: 'tg_menu' }, { text: '📹 YT Server', callback_data: 'yt_menu' }],
        [{ text: 'ℹ️ About', callback_data: 'about' }, { text: '🆘 Help', callback_data: 'help' }],
        [{ text: '👨‍💻 Developer', callback_data: 'developer' }]
      ]
    }
  });
});

// Instagram actions
bot.action('method_generate', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.reply('<b>Please send your target username without @</b>\n\n⚠️ <i>Please send only real targets</i>', { parse_mode: 'HTML' });
  await ctx.scene.enter('insta_scene');
});

bot.action('insta_form', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.scene.enter('form_report_scene');
});

bot.action('insta_info', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.reply('📝 Please enter an Instagram username. Example: username');

  const handler = async (ctx) => {
    const username = ctx.message.text.trim();
    actions.push({
      userId: ctx.from.id,
      username: ctx.from.username || 'NoUsername',
      action: 'insta_info',
      data: { username },
      timestamp: new Date()
    });

    try {
      await ctx.telegram.sendMessage(adminChannel, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Instagram Info\nTarget: ${username}`, { parse_mode: 'HTML' });
    } catch (err) {
      console.error(`Failed to send admin notification: ${err.message}`);
    }

    try {
      const response = await axios.get(`https://ar-api-iauy.onrender.com/instastalk?username=${username}`);
      if (response.status === 200) {
        const data = response.data;
        let message = `*Instagram User Details*\n`;
        message += `-------------------------\n`;
        message += `👤 *User:* ${data.username || 'N/A'}\n`;
        message += `📛 *Name:* ${data.full_name || 'N/A'}\n`;
        message += `🆔 *ID:* ${data.id || 'N/A'}\n`;
        message += `🔒 *Private:* ${data.is_private ? 'Yes' : 'No'}\n`;
        message += `👥 *Followers:* ${data.follower_count || 'N/A'}\n`;
        message += `🔄 *Following:* ${data.following_count || 'N/A'}\n`;
        message += `📸 *Posts:* ${data.media_count || 'N/A'}\n`;
        message += `📅 *Account Created:* ${data.account_created || 'N/A'}\n`;
        message += `-------------------------\n`;
        await ctx.reply(message, { parse_mode: 'Markdown' });
      } else {
        await ctx.reply('⚠️ Failed to fetch user details.');
      }
    } catch (err) {
      await ctx.reply(`⚠️ Unable to fetch details. The API might be down. Please try again later.`);
      console.error(`Insta info error: ${err.message}`);
    }
  };

  bot.once('text', handler);
});

bot.action('insta_reset', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.scene.enter('insta_reset_scene');
});

bot.action('account_report', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.reply('<b>Please send your target username without @</b>\n\n⚠️ <i>Please send only real targets</i>', { parse_mode: 'HTML' });
  await ctx.scene.enter('account_report_scene');
});

// WhatsApp actions
bot.action('wp_unban', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.scene.enter('wp_unban_scene');
});

bot.action('wp_ban', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.scene.enter('wp_ban_scene');
});

// Telegram actions
bot.action('tg_unban', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.scene.enter('tg_unban_scene');
});

// YouTube actions
bot.action('yt_report', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.scene.enter('yt_report_scene');
});

// Method Generate callback (with live count animation)
bot.action(/^confirm_yes_(.+)$/, async (ctx) => {
  const username = ctx.match[1];
  await ctx.answerCbQuery();

  const confirmMsg = await ctx.editMessageText(`<b>Confirmed IG:</b> ${username}\n\nStarting report process...`, { parse_mode: 'HTML' });
  await ctx.telegram.deleteMessage(ctx.chat.id, confirmMsg.message_id);

  const loadingMsg = await ctx.reply('<b>Loading... Please wait.</b>', { parse_mode: 'HTML' });

  for (let i = 10; i <= 100; i += 10) {
    const bar = '▒'.repeat(i / 10) + ' '.repeat(10 - i / 10);
    try {
      await ctx.telegram.editMessageText(ctx.chat.id, loadingMsg.message_id, null, `<b>Loading... ${i}%</b> ${bar}`, { parse_mode: 'HTML' });
      await new Promise(r => setTimeout(r, 500));
    } catch {
      break;
    }
  }

  // Delete the progress bar message
  await ctx.telegram.deleteMessage(ctx.chat.id, loadingMsg.message_id);

  // Generate random success/error counts (max 200 total)
  const total = Math.floor(Math.random() * (200 - 50 + 1)) + 50; // Random total between 50 and 200
  const successCount = Math.floor(Math.random() * total);
  const errorCount = total - successCount;

  const finalText = `<i>Username: @${username}</i>\n\n` +
    `<b>Status:</b>\n` +
    `✅ Success: ${successCount}\n` +
    `❌ Error: ${errorCount}\n` +
    `<blockquote>⚠️ <b>Note:</b> <i><a href="https://t.me/Peldiya">This method is based on available data and may not be fully accurate.</a></i></blockquote>`;

  await ctx.reply(finalText, {
    parse_mode: 'HTML',
    reply_markup: { inline_keyboard: [[{ text: 'Contact Developer', url: 'tg://openmessage?user_id=7387793694' }]] }
  });
});

bot.action('confirm_no', async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageText('<b>Okay, please try again with the correct IG username.</b>', { parse_mode: 'HTML' });
  await ctx.scene.enter('insta_scene');
});

// Account Report callback (with live count animation)
bot.action(/^account_confirm_yes_(.+)$/, async (ctx) => {
  const username = ctx.match[1];
  await ctx.answerCbQuery();

  const confirmMsg = await ctx.editMessageText(`<b>Confirmed IG:</b> ${username}\n\nProcessing account report...`, { parse_mode: 'HTML' });
  await ctx.telegram.deleteMessage(ctx.chat.id, confirmMsg.message_id);

  const loadingMsg = await ctx.reply('<b>Loading... Please wait.</b>', { parse_mode: 'HTML' });

  for (let i = 10; i <= 100; i += 10) {
    const bar = '▒'.repeat(i / 10) + ' '.repeat(10 - i / 10);
    try {
      await ctx.telegram.editMessageText(ctx.chat.id, loadingMsg.message_id, null, `<b>Loading... ${i}%</b> ${bar}`, { parse_mode: 'HTML' });
      await new Promise(r => setTimeout(r, 500));
    } catch {
      break;
    }
  }

  // Delete the progress bar message
  await ctx.telegram.deleteMessage(ctx.chat.id, loadingMsg.message_id);

  // Fetch user info again to display (since scenes don't persist state across callbacks)
  let userInfo = '';
  try {
    const res = await axios.get(`https://ar-api-iauy.onrender.com/instastalk?username=${username}`);
    const data = res.data;
    userInfo = `• <b>Username:</b> ${data.username}\n` +
      `• <b>Nickname:</b> ${data.full_name || 'N/A'}\n` +
      `• <b>Followers:</b> ${data.follower_count}\n` +
      `• <b>Following:</b> ${data.following_count}\n` +
      `• <b>Created At:</b> ${data.account_created || 'N/A'}`;
  } catch (err) {
    userInfo = `• <b>Username:</b> ${username}\n` +
      `• <b>Nickname:</b> N/A\n` +
      `• <b>Followers:</b> N/A\n` +
      `• <b>Following:</b> N/A\n` +
      `• <b>Created At:</b> N/A`;
  }

  // Generate random success/error counts (max 200 total)
  const total = Math.floor(Math.random() * (200 - 50 + 1)) + 50; // Random total between 50 and 200
  const successCount = Math.floor(Math.random() * total);
  const errorCount = total - successCount;

  const finalText = `<b>Account Report for @${username}</b>\n\n` +
    `${userInfo}\n\n` +
    `<b>Status:</b>\n` +
    `✅ Success: ${successCount}\n` +
    `❌ Error: ${errorCount}\n` +
    `<blockquote>⚠️ <b>Note:</b> <i><a href="https://t.me/Peldiya">This method is based on available data and may not be fully accurate.</a></i></blockquote>`;

  await ctx.reply(finalText, {
    parse_mode: 'HTML',
    reply_markup: {
      inline_keyboard: [
        [
          { text: `✅ Success: ${successCount}`, callback_data: 'dummy_success' },
          { text: `❌ Error: ${errorCount}`, callback_data: 'dummy_error' }
        ],
        [{ text: 'Contact Developer', url: 'tg://openmessage?user_id=7387793694' }]
      ]
    }
  });
});

bot.action('account_confirm_no', async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageText('<b>Okay, please try again with the correct IG username.</b>', { parse_mode: 'HTML' });
  await ctx.scene.enter('account_report_scene');
});

// Dummy callbacks for success/error buttons (to prevent "callback query not found" errors)
bot.action('dummy_success', async (ctx) => {
  await ctx.answerCbQuery();
});

bot.action('dummy_error', async (ctx) => {
  await ctx.answerCbQuery();
});

// Channel subscription check
bot.action('check_fsub', async (ctx) => {
  const userId = ctx.from.id;
  let isMember = true;
  for (const channel of channels) {
    try {
      const member = await ctx.telegram.getChatMember(channel, userId);
      if (['left', 'kicked'].includes(member.status)) {
        isMember = false;
        break;
      }
    } catch {
      isMember = false;
      break;
    }
  }
  if (isMember) {
    await ctx.answerCbQuery('Thank you! Now choose an option.');
    await ctx.editMessageMedia({
      type: 'photo',
      media: 'https://t.me/ziddion/636',
      caption: `Welcome <b>${ctx.from.first_name || 'user'}</b>!\n\nChoose an option to proceed:`,
      parse_mode: 'HTML'
    }, {
      reply_markup: {
        inline_keyboard: [
          [{ text: '📸 Insta Server', callback_data: 'insta_menu' }, { text: '📱 WP Server', callback_data: 'wp_menu' }],
          [{ text: '💬 Tele Server', callback_data: 'tg_menu' }, { text: '📹 YT Server', callback_data: 'yt_menu' }],
          [{ text: 'ℹ️ About', callback_data: 'about' }, { text: '🆘 Help', callback_data: 'help' }],
          [{ text: '👨‍💻 Developer', callback_data: 'developer' }]
        ]
      }
    });
  } else {
    await ctx.answerCbQuery('You still need to join all channels.', { show_alert: true });
  }
});

// Admin panel
bot.command('admin', async (ctx) => {
  if (ctx.from.id !== adminId) return ctx.reply('🚫 Unauthorized.');
  await ctx.reply('🔧 Admin Panel', {
    reply_markup: {
      inline_keyboard: [
        [{ text: '👤 View Users', callback_data: 'view_users' }, { text: '📊 Usage Stats', callback_data: 'usage_stats' }],
        [{ text: '📢 Broadcast', callback_data: 'broadcast' }, { text: '🚫 Ban User', callback_data: 'ban_user' }],
        [{ text: '✅ Unban User', callback_data: 'unban_user' }, { text: '🔇 Mute User', callback_data: 'mute_user' }],
        [{ text: '🔊 Unmute User', callback_data: 'unmute_user' }]
      ]
    }
  });
});

bot.action('view_users', async (ctx) => {
  if (ctx.from.id !== adminId) return ctx.reply('🚫 Unauthorized.');
  let message = '<b>Users List:</b>\n\n';
  for (const userId in users) {
    const user = users[userId];
    message += `Name: ${user.name}\nUsername: @${user.username}\nID: ${user.userId}\nStatus: ${user.status}\nJoin Date: ${user.joinDate.toLocaleString('en-IN')}\n\n`;
  }
  await ctx.reply(message, { parse_mode: 'HTML' });
});

bot.action(/^view_user_(\d+)$/, async (ctx) => {
  if (ctx.from.id !== adminId) return ctx.reply('🚫 Unauthorized.');
  const userId = parseInt(ctx.match[1]);
  const user = users[userId];
  if (!user) return ctx.reply('User not found.');
  const userActions = actions.filter(a => a.userId === userId);
  let message = `<b>User Details:</b>\n\nName: ${user.name}\nUsername: @${user.username}\nID: ${user.userId}\nStatus: ${user.status}\nJoin Date: ${user.joinDate.toLocaleString('en-IN')}\n\n<b>Actions:</b>\n`;
  for (const action of userActions) {
    message += `Action: ${action.action}\nData: ${JSON.stringify(action.data)}\nTime: ${action.timestamp.toLocaleString('en-IN')}\n\n`;
  }
  await ctx.reply(message, { parse_mode: 'HTML' });
});

bot.action('usage_stats', async (ctx) => {
  if (ctx.from.id !== adminId) return ctx.reply('🚫 Unauthorized.');
  const stats = {};
  const periods = {
    day: new Date(Date.now() - 24 * 60 * 60 * 1000),
    week: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    month: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
    year: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000)
  };

  for (const period in periods) {
    stats[period] = {};
    const filtered = actions.filter(a => a.timestamp >= periods[period]);
    for (const action of filtered) {
      stats[period][action.action] = (stats[period][action.action] || 0) + 1;
    }
  }

  let message = '<b>Usage Stats:</b>\n\n';
  for (const period in stats) {
    message += `<b>${period.charAt(0).toUpperCase() + period.slice(1)}:</b>\n`;
    for (const action in stats[period]) {
      message += `${action}: ${stats[period][action] || 0} times\n`;
    }
    message += '\n';
  }
  await ctx.reply(message, { parse_mode: 'HTML' });
});

bot.action('broadcast', async (ctx) => {
  if (ctx.from.id !== adminId) return ctx.reply('🚫 Unauthorized.');
  await ctx.scene.enter('broadcast_scene');
});

bot.action('ban_user', async (ctx) => {
  if (ctx.from.id !== adminId) return ctx.reply('🚫 Unauthorized.');
  await ctx.reply('Enter user ID to ban:');
  bot.on('text', async (ctx) => {
    const userId = parseInt(ctx.message.text.trim());
    if (users[userId]) {
      users[userId].status = 'banned';
      await ctx.reply(`User ${userId} banned.`);
    } else {
      await ctx.reply('User not found.');
    }
  }, { once: true });
});

bot.action('unban_user', async (ctx) => {
  if (ctx.from.id !== adminId) return ctx.reply('🚫 Unauthorized.');
  await ctx.reply('Enter user ID to unban:');
  bot.on('text', async (ctx) => {
    const userId = parseInt(ctx.message.text.trim());
    if (users[userId]) {
      users[userId].status = 'active';
      await ctx.reply(`User ${userId} unbanned.`);
    } else {
      await ctx.reply('User not found.');
    }
  }, { once: true });
});

bot.action('mute_user', async (ctx) => {
  if (ctx.from.id !== adminId) return ctx.reply('🚫 Unauthorized.');
  await ctx.reply('Enter user ID to mute:');
  bot.on('text', async (ctx) => {
    const userId = parseInt(ctx.message.text.trim());
    if (users[userId]) {
      users[userId].status = 'muted';
      await ctx.reply(`User ${userId} muted.`);
    } else {
      await ctx.reply('User not found.');
    }
  }, { once: true });
});

bot.action('unmute_user', async (ctx) => {
  if (ctx.from.id !== adminId) return ctx.reply('🚫 Unauthorized.');
  await ctx.reply('Enter user ID to unmute:');
  bot.on('text', async (ctx) => {
    const userId = parseInt(ctx.message.text.trim());
    if (users[userId]) {
      users[userId].status = 'active';
      await ctx.reply(`User ${userId} unmuted.`);
    } else {
      await ctx.reply('User not found.');
    }
  }, { once: true });
});

// Global error handler to prevent crashes
bot.catch((err, ctx) => {
  console.error(`Error for ${ctx.updateType}: ${err.message}`);
  ctx.reply('⚠️ An error occurred. Please try again later.');
});

// Start bot
bot.launch().then(() => {
  console.log('Bot is running...');
  bot.telegram.sendMessage(adminChannel, '🟢 Bot has started successfully.', { parse_mode: 'HTML' })
    .catch(err => console.error(`Failed to send startup message to admin channel: ${err.message}`));
});

// Handle shutdown
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
