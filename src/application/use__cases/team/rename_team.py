from src.application.ports.team_port import TeamRepositoryPort


class RenameTeamUseCase:
    def __init__(self, team_repository: TeamRepositoryPort):
        self.team_repository = team_repository

    def execute(self, id: int, name: str):
        team = self.team_repository.get_by_id(id)
        team.rename(name)
        self.team_repository.save(team)
