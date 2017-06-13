__author__ = 'yuwenhao'

import numpy as np
from gym import utils
from gym.envs.dart import dart_env


class DartWalker3dRestrictedEnv(dart_env.DartEnv, utils.EzPickle):
    def __init__(self):
        self.control_bounds = np.array([[1.0]*15,[-1.0]*15])
        self.action_scale = np.array([100.0]*15)
        self.action_scale[[-1,-2,-7,-8]] = 20
        self.action_scale[[0, 1, 2]] = 40
        obs_dim = 41

        self.t = 0

        dart_env.DartEnv.__init__(self, 'walker3d_waist_restricted.skel', 8, obs_dim, self.control_bounds, disableViewer=True)

        self.robot_skeleton.set_self_collision_check(True)

        self.origin_q = self.robot_skeleton.q
        self.fatigue_percentage = 0.3 # start counting fatigue from 30%
        self.fatigue_count = np.zeros(len(self.robot_skeleton.q))

        for i in range(1, len(self.dart_world.skeletons[0].bodynodes)):
            self.dart_world.skeletons[0].bodynodes[i].set_friction_coeff(0)
        self.chaser_x = 0
        utils.EzPickle.__init__(self)

    def advance(self, a):
        clamped_control = np.array(a)
        for i in range(len(clamped_control)):
            if clamped_control[i] > self.control_bounds[0][i]:
                clamped_control[i] = self.control_bounds[0][i]
            if clamped_control[i] < self.control_bounds[1][i]:
                clamped_control[i] = self.control_bounds[1][i]
        tau = np.zeros(self.robot_skeleton.ndofs)
        tau[6:] = clamped_control * self.action_scale

        self.do_simulation(tau, self.frame_skip)

    def _step(self, a):
        pre_state = [self.state_vector()]

        posbefore = self.robot_skeleton.bodynodes[0].com()[0]
        self.advance(a)

        posafter = self.robot_skeleton.bodynodes[0].com()[0]
        height = self.robot_skeleton.bodynodes[0].com()[1]
        side_deviation = self.robot_skeleton.bodynodes[0].com()[2]

        upward = np.array([0, 1, 0])
        upward_world = self.robot_skeleton.bodynodes[1].to_world(np.array([0, 1, 0])) - self.robot_skeleton.bodynodes[1].to_world(np.array([0, 0, 0]))
        upward_world /= np.linalg.norm(upward_world)
        ang_cos_uwd = np.dot(upward, upward_world)
        ang_cos_uwd = np.arccos(ang_cos_uwd)

        forward = np.array([1, 0, 0])
        forward_world = self.robot_skeleton.bodynodes[1].to_world(np.array([1, 0, 0])) - self.robot_skeleton.bodynodes[1].to_world(np.array([0, 0, 0]))
        forward_world /= np.linalg.norm(forward_world)
        ang_cos_fwd = np.dot(forward, forward_world)
        ang_cos_fwd = np.arccos(ang_cos_fwd)

        contacts = self.dart_world.collision_result.contacts
        total_force_mag = 0
        for contact in contacts:
            total_force_mag += np.square(contact.force).sum()

        joint_limit_penalty = 0
        for j in [-3, -9]:
            if (self.robot_skeleton.q_lower[j] - self.robot_skeleton.q[j]) > -0.05:
                joint_limit_penalty += abs(1.5)
            if (self.robot_skeleton.q_upper[j] - self.robot_skeleton.q[j]) < 0.05:
                joint_limit_penalty += abs(1.5)

        alive_bonus = 1.0
        vel_rew = 2.0 * (posafter - posbefore) / self.dt
        action_pen = 1e-2 * np.square(a).sum()
        joint_pen = 0 * joint_limit_penalty
        deviation_pen = 1e-3 * abs(side_deviation)
        reward = vel_rew + alive_bonus - action_pen - joint_pen - deviation_pen

        #print(vel_rew/2)

        action_vio = np.sum(np.exp(np.max([(a-self.control_bounds[0]*1.5), [0]*15], axis=0)) - [1]*15)
        action_vio += np.sum(np.exp(np.max([(self.control_bounds[1]*1.5-a), [0]*15], axis=0)) - [1]*15)
        reward -= 0.1*action_vio

        reward -= 0.05*(abs(ang_cos_uwd)+abs(ang_cos_fwd))

        '''q_diff = np.abs(self.robot_skeleton.q - self.origin_q)
        fatigue_reward = 0
        for dofid in range(len(q_diff)):
            dof_range = self.robot_skeleton.q_upper[dofid] - self.robot_skeleton.q_lower[dofid]
            if q_diff[dofid]/dof_range < self.fatigue_percentage:
                self.fatigue_count[dofid] = 0
            else:
                self.fatigue_count[dofid] += 1
                if self.fatigue_count[dofid] > 100:
                    fatigue_reward += np.exp(0.01*self.fatigue_count[dofid])-1
        reward -= fatigue_reward'''

        #reward -= 1e-7 * total_force_mag

        #div = self.get_div()
        #reward -= 1e-1 * np.min([(div**2), 10])
        
        self.chaser_x += self.dt * 0.1
        if self.chaser_x > posafter: # if the chaser catches up
            reward -= (self.chaser_x - posafter)

        self.t += self.dt

        s = self.state_vector()
        done = not (np.isfinite(s).all() and (np.abs(s[2:]) < 100).all() and
                    (height > 1.05) and (height < 2.0) and (abs(ang_cos_uwd) < 10.84) and (abs(ang_cos_fwd) < 10.84))

        if done:
            reward = 0

        ob = self._get_obs()

        foot1_com = self.robot_skeleton.bodynode('h_foot').com()
        foot2_com = self.robot_skeleton.bodynode('h_foot_left').com()
        robot_com = self.robot_skeleton.com()
        com_foot_offset1 = robot_com - foot1_com
        com_foot_offset2 = robot_com - foot2_com

        return ob, reward, done, {'pre_state':pre_state, 'vel_rew':vel_rew, 'action_pen':action_pen, 'joint_pen':joint_pen, 'deviation_pen':deviation_pen, 'aux_pred':np.hstack([com_foot_offset1, com_foot_offset2, [reward]]), 'done_return':done}

    def _get_obs(self):
        state =  np.concatenate([
            self.robot_skeleton.q[1:],
            np.clip(self.robot_skeleton.dq,-10,10),
            #[self.t]
        ])

        return state

    def reset_model(self):
        self.dart_world.reset()
        qpos = self.robot_skeleton.q + self.np_random.uniform(low=-.005, high=.005, size=self.robot_skeleton.ndofs)
        qvel = self.robot_skeleton.dq + self.np_random.uniform(low=-.005, high=.005, size=self.robot_skeleton.ndofs)
        sign = np.sign(np.random.uniform(-1, 1))
        qpos[9] = sign * self.np_random.uniform(low=0.0, high=0.1, size=1)
        qpos[15] = -sign * self.np_random.uniform(low=0.0, high=0.1, size=1)
        self.set_state(qpos, qvel)
        self.t = 0
        self.chaser_x = -0.2

        self.fatigue_count = np.zeros(len(self.robot_skeleton.q))

        return self._get_obs()

    def viewer_setup(self):
        if not self.disableViewer:
            self._get_viewer().scene.tb.trans[2] = -5.5