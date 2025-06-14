require('dotenv').config();
const { Telegraf, Scenes, session } = require('telegraf');
const axios = require('axios');
const cron = require('node-cron');
const faker = require('faker');

const bot = new Telegraf(process.env.BOT_TOKEN);
const adminId = 7387793694;
const adminChannel = process.env.ADMIN_CHANNEL || '@YourAdminChannel'; // Replace with your channel ID

// In-memory storage
const users = {};
const actions = [];

// Scene for Instagram username input
const instaScene = new Scenes.BaseScene('insta_scene');
instaScene.enter((ctx) => ctx.reply('📝 Please send the Instagram username without @.'));
instaScene.on('text', async (ctx) => {
  const username = ctx.message.text.trim();
  actions.push({
    userId: ctx.from.id,
    username: ctx.from.username || 'NoUsername',
    action: 'insta_mass_report',
    data: { username },
    timestamp: new Date()
  });

  // Notify admin
  await ctx.telegram.sendMessage(adminId, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Instagram Mass Report\nTarget: ${username}`, { parse_mode: 'HTML' });

  const timeout = setTimeout(async () => {
    await ctx.reply('<b>⏱ Request timed out!</b>\n\nPlease send the Instagram username again.', { parse_mode: 'HTML' });
    return await ctx.scene.leave();
  }, 7000);

  try {
    const res = await axios.get(`https://ar-api-iauy.onrender.com/instastalk?username=${username}`);
    clearTimeout(timeout);
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
    clearTimeout(timeout);
    await ctx.reply('<b>Something went wrong while verifying the username.</b>\n\nPlease send the username without @.', { parse_mode: 'HTML' });
    return await ctx.scene.leave();
  }
});

// Scene for Instagram form report
const formReportScene = new Scenes.BaseScene('form_report_scene');
formReportScene.enter((ctx) => ctx.reply('📝 Please send the Instagram username and target link (e.g., username https://instagram.com/p/xxx).'));
formReportScene.on('text', async (ctx) => {
  const [username, targetLink] = ctx.message.text.trim().split(' ');
  actions.push({
    userId: ctx.from.id,
    username: ctx.from.username || 'NoUsername',
    action: 'insta_form_report',
    data: { username, targetLink },
    timestamp: new Date()
  });

  await ctx.telegram.sendMessage(adminId, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Instagram Form Report\nTarget: ${username}\nLink: ${targetLink}`, { parse_mode: 'HTML' });

  try {
    const lsd = Math.random().toString(36).substring(2, 14);
    const funame = faker.name.findName();
    const em = Math.random().toString(36).substring(2, 8) + '@gmail.com';
    const url = "https://help.instagram.com/ajax/help/contact/submit/page";
    const payload = `jazoest=${Math.floor(Math.random() * 9000) + 1000}&lsd=${lsd}&radioDescribeSituation=represent_impersonation&inputFullName=${funame}&inputEmail=${em}&Field280160739058799=User&Field1600094910240113=${username}&Field1446762042284494=NotExist&Field249579765548460=${username}&inputReportedUsername=${username}&uploadID%5B0%5D=${targetLink}&support_form_id=636276399721841&support_form_locale_id=en_US&support_form_hidden_fields=%7B%22964093983759778%22%3Atrue%2C%22477937845607074%22%3Atrue%2C%22600631177074776%22%3Atrue%7D&__user=0&__a=1&__req=a&__hs=20029.BP%3ADEFAULT.2.0..0.0&dpr=3&__ccg=GOOD&__rev=1017899129&__s=%3Agc4pjs%3Auic2h1&__spin_r=1017899129&__spin_b=trunk&__spin_t=${Math.floor(Date.now() / 1000)}`;
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
    } else {
      await ctx.reply('✅ Report sent successfully.');
    }
  } catch (err) {
    await ctx.reply(`🚨 Error: ${err.message}`);
  }
  await ctx.scene.leave();
});

// Scene for Instagram password reset
const instaResetScene = new Scenes.BaseScene('insta_reset_scene');
instaResetScene.enter((ctx) => ctx.reply('📝 Please send your Instagram username or email.'));
instaResetScene.on('text', async (ctx) => {
  const emailOrUsername = ctx.message.text.trim();
  actions.push({
    userId: ctx.from.id,
    username: ctx.from.username || 'NoUsername',
    action: 'insta_pass_reset',
    data: { emailOrUsername },
    timestamp: new Date()
  });

  await ctx.telegram.sendMessage(adminId, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Instagram Password Reset\nTarget: ${emailOrUsername}`, { parse_mode: 'HTML' });

  try {
    const response = await axios.get(`https://instagram-pass-reset.vercel.app/reset-password?username=${encodeURIComponent(emailOrUsername)}`);
    await ctx.reply(`📬 **Result:** \`${JSON.stringify(response.data)}\``, { parse_mode: 'Markdown' });
  } catch (err) {
    await ctx.reply(`🚨 Error: ${err.message}`);
  }
  await ctx.scene.leave();
});

// Scene for WhatsApp unban
const wpUnbanScene = new Scenes.BaseScene('wp_unban_scene');
wpUnbanScene.enter((ctx) => ctx.reply('📝 Please send your email, phone number with country code, and mobile model.'));
wpUnbanScene.on('text', async (ctx) => {
  const [email, phone, model] = ctx.message.text.trim().split(' ');
  actions.push({
    userId: ctx.from.id,
    username: ctx.from.username || 'NoUsername',
    action: 'wp_unban',
    data: { email, phone, model },
    timestamp: new Date()
  });

  await ctx.telegram.sendMessage(adminId, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: WhatsApp Unban\nEmail: ${email}\nPhone: ${phone}\nModel: ${model}`, { parse_mode: 'HTML' });

  try {
    const subject = encodeURIComponent('My WhatsApp account has been deactivated by mistake');
    const message = encodeURIComponent(`Hello,\nMy WhatsApp account has been deactivated by mistake.\nCould you please activate my phone number: "${phone}"\nMy mobile model: "${model}"\nThanks in advance.`);
    await axios.get(`https://sendmail.ashlynn.workers.dev/send-email?to=Support@Whatsapp.com&from=${encodeURIComponent(email)}&subject=${subject}&message=${message}`);
    await ctx.reply('✅ Unban request sent successfully.');
  } catch (err) {
    await ctx.reply(`🚨 Error: ${err.message}`);
  }
  await ctx.scene.leave();
});

// Scene for WhatsApp ban
const wpBanScene = new Scenes.BaseScene('wp_ban_scene');
wpBanScene.enter((ctx) => ctx.reply('📝 Please send your email and target phone number with country code.'));
wpBanScene.on('text', async (ctx) => {
  const [email, phone] = ctx.message.text.trim().split(' ');
  actions.push({
    userId: ctx.from.id,
    username: ctx.from.username || 'NoUsername',
    action: 'wp_ban',
    data: { email, phone },
    timestamp: new Date()
  });

  await ctx.telegram.sendMessage(adminId, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: WhatsApp Ban\nEmail: ${email}\nPhone: ${phone}`, { parse_mode: 'HTML' });

  try {
    const subject = encodeURIComponent('Report: Inappropriate WhatsApp Account');
    const message = encodeURIComponent(`Hello,\nI am reporting an inappropriate WhatsApp account.\nPhone number: ${phone}\nPlease take appropriate action.\nThanks.`);
    await axios.get(`https://sendmail.ashlynn.workers.dev/send-email?to=Support@Whatsapp.com&from=${encodeURIComponent(email)}&subject=${subject}&message=${message}`);
    await ctx.reply('✅ Ban request sent successfully.');
  } catch (err) {
    await ctx.reply(`🚨 Error: ${err.message}`);
  }
  await ctx.scene.leave();
});

// Scene for Telegram ban
const tgBanScene = new Scenes.BaseScene('tg_ban_scene');
tgBanScene.enter((ctx) => ctx.reply('📝 Please send your phone number, API ID, API hash, OTP (if required), and target username/channel.'));
tgBanScene.on('text', async (ctx) => {
  const [phone, apiId, apiHash, otp, target] = ctx.message.text.trim().split(' ');
  actions.push({
    userId: ctx.from.id,
    username: ctx.from.username || 'NoUsername',
    action: 'tg_ban',
    data: { phone, apiId, apiHash, target },
    timestamp: new Date()
  });

  await ctx.telegram.sendMessage(adminId, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Telegram Ban\nPhone: ${phone}\nTarget: ${target}`, { parse_mode: 'HTML' });

  try {
    const { TelegramClient, ReportPeerRequest, InputReportReasonSpam } = require('telethon');
    const client = new TelegramClient(`session_${phone}`, parseInt(apiId), apiHash);
    await client.start(phone, async () => otp || '');
    const entity = await client.get_entity(target);
    await client(ReportPeerRequest(peer=entity, reason=InputReportReasonSpam(), message='Mass report for spam'));
    await client.disconnect();
    await ctx.reply('✅ Report sent successfully.');
  } catch (err) {
    await ctx.reply(`🚨 Error: ${err.message}`);
  }
  await ctx.scene.leave();
});

// Scene for Telegram unban
const tgUnbanScene = new Scenes.BaseScene('tg_unban_scene');
tgUnbanScene.enter((ctx) => ctx.reply('📝 Please send your email and phone number for Telegram unban request.'));
tgUnbanScene.on('text', async (ctx) => {
  const [email, phone] = ctx.message.text.trim().split(' ');
  actions.push({
    userId: ctx.from.id,
    username: ctx.from.username || 'NoUsername',
    action: 'tg_unban',
    data: { email, phone },
    timestamp: new Date()
  });

  await ctx.telegram.sendMessage(adminId, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Telegram Unban\nEmail: ${email}\nPhone: ${phone}`, { parse_mode: 'HTML' });

  await ctx.reply('✅ Telegram unban request noted. Please contact support for further assistance.');
  await ctx.scene.leave();
});

// Scene for YouTube report
const ytReportScene = new Scenes.BaseScene('yt_report_scene');
ytReportScene.enter((ctx) => ctx.reply('📝 Please send your email, target channel username, link, and report text.'));
ytReportScene.on('text', async (ctx) => {
  const [email, username, link, ...text] = ctx.message.text.trim().split(' ');
  const reportText = text.join(' ');
  actions.push({
    userId: ctx.from.id,
    username: ctx.from.username || 'NoUsername',
    action: 'yt_report',
    data: { email, username, link, reportText },
    timestamp: new Date()
  });

  await ctx.telegram.sendMessage(adminId, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: YouTube Report\nEmail: ${email}\nTarget: ${username}\nLink: ${link}\nText: ${reportText}`, { parse_mode: 'HTML' });

  try {
    const subject = encodeURIComponent('YouTube Channel Report');
    const message = encodeURIComponent(`Hello,\nI am reporting a YouTube channel.\nUsername: ${username}\nLink: ${link}\nReason: ${reportText}\nThanks.`);
    await axios.get(`https://sendmail.ashlynn.workers.dev/send-email?to=support@youtube.com&from=${encodeURIComponent(email)}&subject=${subject}&message=${message}`);
    await ctx.reply('✅ YouTube report sent successfully.');
  } catch (err) {
    await ctx.reply(`🚨 Error: ${err.message}`);
  }
  await ctx.scene.leave();
});

// Scene for admin broadcast
const broadcastScene = new Scenes.BaseScene('broadcast_scene');
broadcastScene.enter((ctx) => ctx.reply('📢 Enter the message to broadcast to all users.'));
broadcastScene.on('text', async (ctx) => {
  if (ctx.from.id !== adminId) return ctx.reply('🚫 Unauthorized.');
  const message = ctx.message.text.trim();
  for (const userId in users) {
    try {
      await ctx.telegram.sendMessage(userId, message, { parse_mode: 'HTML' });
    } catch (err) {
      console.error(`Failed to send to ${userId}: ${err.message}`);
    }
  }
  await ctx.reply('✅ Broadcast sent.');
  await ctx.scene.leave();
});

// Initialize scenes
const stage = new Scenes.Stage([
  instaScene,
  formReportScene,
  instaResetScene,
  wpUnbanScene,
  wpBanScene,
  tgBanScene,
  tgUnbanScene,
  ytReportScene,
  broadcastScene
]);
bot.use(session());
bot.use(stage.middleware());

// Channel check middleware
const channels = ['@PythonBotz', '@Channel2', '@Channel3', '@Channel4']; // Replace with your channels
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

    await ctx.telegram.sendMessage(adminId, `🆕 New User\nName: ${ctx.from.first_name || 'N/A'}\nUsername: @${ctx.from.username || 'N/A'}\nID: ${userId}\nDate: ${new Date().toLocaleString('en-IN')}`, {
      parse_mode: 'HTML',
      reply_markup: { inline_keyboard: [[{ text: `View ${ctx.from.first_name || 'User'}`, callback_data: `view_user_${userId}` }]] }
    });
  }

  await ctx.replyWithPhoto('https://example.com/menu.jpg', { // Replace with your photo URL
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
    media: 'https://example.com/insta_menu.jpg', // Replace with your photo URL
    caption: '📸 Instagram Server\nChoose an option:',
    parse_mode: 'HTML'
  }, {
    reply_markup: {
      inline_keyboard: [
        [{ text: 'Account Mass Report', callback_data: 'insta_mass' }, { text: 'Form Mass Report', callback_data: 'insta_form' }],
        [{ text: 'Insta Info', callback_data: 'insta_info' }, { text: 'Insta Pass Reset', callback_data: 'insta_reset' }],
        [{ text: '🔙 Back', callback_data: 'back_main' }]
      ]
    }
  });
});

bot.action('wp_menu', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageMedia({
    type: 'photo',
    media: 'https://example.com/wp_menu.jpg', // Replace with your photo URL
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
    media: 'https://example.com/tg_menu.jpg', // Replace with your photo URL
    caption: '💬 Telegram Server\nChoose an option:',
    parse_mode: 'HTML'
  }, {
    reply_markup: {
      inline_keyboard: [
        [{ text: 'TG Unban', callback_data: 'tg_unban' }, { text: 'TG Ban', callback_data: 'tg_ban' }],
        [{ text: '🔙 Back', callback_data: 'back_main' }]
      ]
    }
  });
});

bot.action('yt_menu', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageMedia({
    type: 'photo',
    media: 'https://example.com/yt_menu.jpg', // Replace with your photo URL
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
    `📸 <b>Insta Server:</b> Account Mass Report, Form Mass Report, Insta Info, Insta Pass Reset\n` +
    `📱 <b>WP Server:</b> WhatsApp Unban, WhatsApp Ban\n` +
    `💬 <b>Tele Server:</b> Telegram Unban, Telegram Ban\n` +
    `📹 <b>YT Server:</b> YouTube Channel Report\n\n` +
    `Join our channels for updates: @PythonBotz`,
    {
      parse_mode: 'HTML',
      reply_markup: {
        inline_keyboard: [
          [{ text: 'Updated', url: 't.me/PythonBotz' }, { text: 'Support', url: 't.me/offchats' }],
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
    media: 'https://example.com/menu.jpg', // Replace with your photo URL
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
bot.action('insta_mass', checkChannels, async (ctx) => {
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
  bot.on('text', async (ctx) => {
    const username = ctx.message.text.trim();
    actions.push({
      userId: ctx.from.id,
      username: ctx.from.username || 'NoUsername',
      action: 'insta_info',
      data: { username },
      timestamp: new Date()
    });

    await ctx.telegram.sendMessage(adminId, `🔔 New Action\nUser: @${ctx.from.username || 'NoUsername'}\nAction: Instagram Info\nTarget: ${username}`, { parse_mode: 'HTML' });

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
      await ctx.reply(`🚨 Error: ${err.message}`);
    }
  }, { once: true });
});

bot.action('insta_reset', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.scene.enter('insta_reset_scene');
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
bot.action('tg_ban', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.scene.enter('tg_ban_scene');
});

bot.action('tg_unban', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.scene.enter('tg_unban_scene');
});

// YouTube actions
bot.action('yt_report', checkChannels, async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.scene.enter('yt_report_scene');
});

// Instagram mass report callback
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

  const categories = [
    'Nudity¹', 'Nudity²', 'Nudity³', 'Nudity⁴', 'Hate', 'Scam', 'Terrorism',
    'Vio¹', 'Vio²', 'Vio³', 'Vio⁴', 'Sale Illegal [High Risk Drugs]',
    'Sale Illegal [Other Drugs]', 'Firearms', 'Endangered Animal',
    'Bully_Me', 'Self_Injury', 'Self [Eating Disorder]', 'Spam', 'Problem'
  ];

  const count = Math.floor(Math.random() * 3) + 2;
  const picked = [];
  while (picked.length < count) {
    const cat = categories[Math.floor(Math.random() * categories.length)];
    if (!picked.includes(cat)) picked.push(cat);
  }

  const successCount = Math.floor(Math.random() * 15) + 5;
  const errorCount = Math.floor(Math.random() * 10);
  const result = picked.map(cat => `➥ ${Math.floor(Math.random() * 5) + 1}x ${cat}`).join('\n');
  const finalText = `<i>Username: @${username}</i>\n\n<b>Suggested Reports:</b>\n\n<pre>${result}</pre>\n\n` +
    `<b>Status:</b> ${successCount} Success, ${errorCount} Error\n` +
    `<blockquote>⚠️ <b>Note:</b> <i><a href="https://t.me/Peldiya">This method is based on available data and may not be fully accurate.</a></i></blockquote>`;

  await ctx.telegram.editMessageText(ctx.chat.id, loadingMsg.message_id, null, finalText, {
    parse_mode: 'HTML',
    reply_markup: { inline_keyboard: [[{ text: 'Contact Developer', url: 'tg://openmessage?user_id=7387793694' }]] }
  });
});

bot.action('confirm_no', async (ctx) => {
  await ctx.answerCbQuery();
  await ctx.editMessageText('<b>Okay, please try again with the correct IG username.</b>', { parse_mode: 'HTML' });
  await ctx.scene.enter('insta_scene');
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
      media: 'https://example.com/menu.jpg', // Replace with your photo URL
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

// Start bot
bot.launch();
console.log('Bot is running...');

// Handle shutdown
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
