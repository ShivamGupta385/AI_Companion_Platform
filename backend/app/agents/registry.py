from backend.app.agents.aria.agent import AriaAgent
from backend.app.agents.noor.agent import NoorAgent
from backend.app.agents.rene.agent import ReneAgent
from backend.app.agents.max.agent import MaxAgent
from backend.app.agents.victor.agent import VictorAgent


AGENTS = {
    "Aria": AriaAgent(),
    "Noor": NoorAgent(),
    "Rene": ReneAgent(),
    "Max": MaxAgent(),
    "Victor": VictorAgent(),
}