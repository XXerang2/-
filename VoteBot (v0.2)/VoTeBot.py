import discord
from discord.ext import commands
import asyncio
import time

TOKEN = "YOUR_BOT_TOKEN"

intents = discord.Intents.default()
intents.message_content = True  
bot = commands.Bot(command_prefix="!", intents=intents)

class PollView(discord.ui.View):
    def __init__(self, question, timeout=600):  # 기본 10분 (600초)
        super().__init__(timeout=timeout)
        self.question = question
        self.votes = {"🟦": [], "🟥": []}  # 사용자 리스트로 저장
        self.user_votes = {}  # {유저ID: 선택}
        self.message = None
        self.start_time = time.time()
        self.end_time = self.start_time + timeout
        self.total_steps = 10  # 진행바 단계
        self.image_urls = {
            "🟦": "YOUR_APPROVE_IMAGE_URL",  # 왼쪽 선택 이미지
            "🟥": "YOUR_APPROVE_IMAGE_URL",  # 오른쪽 선택 이미지
        }
        self.poll_active = True  # 투표 활성화 여부

    def get_progress_bar(self):
        """현재 남은 시간에 따라 진행바 이모지 표시"""
        elapsed_time = time.time() - self.start_time
        remaining_steps = max(0, self.total_steps - int((elapsed_time / (self.end_time - self.start_time)) * self.total_steps))
        
        if remaining_steps == 0:
            return "👩‍🏫【투표 종료】"
        return "⬜" * remaining_steps + "⏪" + "⬛" * (self.total_steps - remaining_steps - 1)

    async def update_message(self):
        """투표 메시지를 업데이트하여 남은 시간을 반영"""
        if self.message and self.poll_active:
            remaining_time = max(int(self.end_time - time.time()), 0)
            minutes, seconds = divmod(remaining_time, 60)
            progress_bar = self.get_progress_bar()

            embed = discord.Embed(
                title="⏳【투표 진행 중】",
                description=f"💁‍♀️【질문】:**{self.question}**\n\n{progress_bar}\n⏰ 【남은 시간】: {minutes}분 {seconds}초",
                color=discord.Color.blue()
            )

            for option, users in self.votes.items():
                voters = ", ".join(users) if users else "없음"
                embed.add_field(name=f"{option} ({len(users)} 표)", value=f"👤 {voters}", inline=False)

            await self.message.edit(embed=embed, view=self)

    async def on_timeout(self):
        """투표 종료 시 버튼 비활성화 및 결과 발표"""
        self.poll_active = False
        for button in self.children:
            button.disabled = True  # 버튼 비활성화

        result_embed = discord.Embed(
            title="👩‍🏫【투표 종료】",
            description=f"**{self.question}**",
            color=discord.Color.red()
        )

        for option, users in self.votes.items():
            voters = ", ".join(users) if users else "없음"
            result_embed.add_field(name=f"{option} ({len(users)} 표)", value=f"👤 {voters}", inline=False)

        if self.message:
            await self.message.edit(embed=result_embed, view=self)

    @discord.ui.button(label="🟦 왼쪽", style=discord.ButtonStyle.success)
    async def vote_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vote(interaction, "🟦")

    @discord.ui.button(label="🟥 오른쪽", style=discord.ButtonStyle.danger)
    async def vote_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vote(interaction, "🟥")

    async def vote(self, interaction: discord.Interaction, option: str):
        """투표를 처리하는 함수"""
        if not self.poll_active:
            await interaction.response.send_message("⚠️ 투표가 종료되었습니다!", ephemeral=True)
            return

        user_id = interaction.user.id
        username = interaction.user.display_name  # 유저 이름 가져오기

        if user_id in self.user_votes:
            prev_vote = self.user_votes[user_id]
            self.votes[prev_vote].remove(username)  # 기존 투표 삭제

        self.votes[option].append(username)  # 새 투표 추가
        self.user_votes[user_id] = option

        embed = discord.Embed(
            title="⏳【투표 진행 중】",
            description=f"💁‍♀️【질문】: **{self.question}**\n\n{self.get_progress_bar()}",
            color=discord.Color.blue()
        )

        for opt, users in self.votes.items():
            voters = ", ".join(users) if users else "없음"
            embed.add_field(name=f"{opt} ({len(users)} 표)", value=f"👤 {voters}", inline=False)

        # 버튼 클릭 시 이미지 추가
        if option in self.image_urls:
            embed.set_image(url=self.image_urls[option])

        await interaction.response.edit_message(embed=embed, view=self)

@bot.command()
async def 투표(ctx, *, question):
    """투표 시작"""
    view = PollView(question)
    embed = discord.Embed(
        title="📢 【투표 시작】",
        description=f"💁‍♀️【질문】: **{question}**\n\n⏰【시간 제한】: 10분",
        color=discord.Color.green()
    )
    embed.add_field(name="🟦", value="왼쪽", inline=True)
    embed.add_field(name="🟥", value="오른쪽", inline=True)

    message = await ctx.send(embed=embed, view=view)
    view.message = message

    # 남은 시간 업데이트 루프 실행
    while time.time() < view.end_time:
        await asyncio.sleep(60)  # 1분마다 업데이트
        await view.update_message()

    await view.on_timeout()  # 투표 종료 실행

bot.run(TOKEN)
