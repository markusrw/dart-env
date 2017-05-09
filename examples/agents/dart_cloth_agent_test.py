__author__ = 'alexander_clegg'

import gym
import numpy as np
import time

import joblib
import tensorflow as tf

if __name__ == '__main__':
    #load policy
    
    #standard reacher: moved cloth 
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/reacher_sphere_movedcloth_2017_04_28_10_02_27_0001/params.pkl"
    
    #standard reacher: no simulated cloth
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/reacher_sphere_noclothsim_2017_04_29_13_31_56_0001/params.pkl"
    
    #self terminating (1st try w/ small penalty for deformation)
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/reacher_selfterminating_2017_04_26_21_00_09_0001/params.pkl"
    
    #cloth trial 1?
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/reacher_cloth1st(slow)_2017_04_27_11_06_16_0001/params.pkl"
    
    #cloth trial alternate reward
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/reacher_cloth_alternatereward_2017_04_28_00_12_56_0001/params.pkl"
    
    #hemisphere no cloth test
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/experiment_2017_05_01_noclothhemisphere_statereward/params.pkl"
    
    #sphere samples with cloth test (-2000 penalty)
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/reacher_sphere_cloth(-2000 penalty)_2017_04_30_12_15_00_0001/params.pkl"
    
    #Cloth reacher new reward
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/experiment_2017_05_03_clothreacher_disprewardtuned/params.pkl"
    
    #warm start
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/experiment_2017_05_04_clothreacher_warmstart_hemispherestatereward/params.pkl"
    
    #vanilla reacher new reward
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/experiment_2017_05_02_reacher_displacementreward_nocloth/params.pkl"
    
    #warm start stabilizer trial:
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/experiment_2017_05_04_reacher_warmstart_sphere_state2stable_prox/params.pkl"
    
    #warm start moving cloth trial 1 (~600 iter)
    #filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/experiment_2017_05_04_reacher_warmstart_stablesphere2movingcloth/params.pkl"
    
    #warm start moving cloth trial 2 (1500 iter)
    filename = "/home/alexander/Documents/dev/rllab/data/local/experiment/experiment_2017_05_08_reacher_warmstart_stablesphere2movingcloth3/params.pkl"
    

    with tf.Session() as sess:
        data = joblib.load(filename)
        policy = data['policy']
        #loadenv = data['env']
    print(policy)

    #construct env
    #env = gym.make('DartClothSphereTube-v1')
    #env = gym.make('DartReacher-v1')
    env = gym.make('DartClothReacher-v1')
    env.reset()

    #Cloth sphere testing
    '''
    ppos = np.array([0.1,0,0])
    for i in range(1000):
        #print("ppos = " + str(ppos))
        a = ppos/(-np.linalg.norm(ppos))
        #print("a = " + str(a))
        ppos = env.step(a)[0][:3]
        #print(env.step([0,0.98,0.1]))
        env.render()
    '''
    '''        
    for i in range(1000):
        env.reset()
        env.render()
        time.sleep(0.5)
        ppos = np.array([0.1,0,0])
        for j in range(100):
            a = ppos/(-np.linalg.norm(ppos))
            ppos = env.step(a)[0][:3]
            env.render()
            time.sleep(0.1)
        #time.sleep(0.5)
    '''
    
    for i in range(100000):
        #print("about to reset")
        o = env.reset()
        #print("done reset")
        env.render()
        #time.sleep(0.5)
        for j in range(500):
            a, a_info = policy.get_action(o)
            #a = np.array([-1,-0,-0,-0,-0.])
            s_info = env.step(a)
            o = s_info[0]
            done = s_info[2]
            #print("o = " + str(o))
            #time.sleep(0.1)
            env.render()
            if done is True:
                time.sleep(0.5)
                break
            #exit()
            

    env.render(close=True)