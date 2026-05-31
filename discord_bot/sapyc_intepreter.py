import discord

class SAPYC_Intepreter:
    def __init__(self):
        pass

    async def history_log(message: discord.Message,
                          *args
                          ) -> None:
        pass


    async def intepret_sapyc(self,
                             message: discord.Message,
                             cmd: str
                             ) -> None:
        cmd = cmd.split("/")[0]
        command_breakdown = cmd.split("<")
        command_type_breakdown = command_breakdown[0].split(";") 
        cmd_domain = command_type_breakdown[0]
        cmd_space = command_type_breakdown[1]
        cmd_name = command_type_breakdown[2]
        command_content_breakdown = command_breakdown[1].split(";")
