import {
    REQUEST_BROWSER_LOGIN,
    GET_LOGIN,
    SET_CONFIG,
    SET_LOGIN,
    REQUEST_USER_LOGIN,
    GET_COURSES,
    SET_COURSES, UPDATE_COURSE, REMOVE_COURSES
} from "./actions";
import moment from "moment";

const initialState = {
    userLogin: false,
    browserLogin: false,
    userLoading: true,
    browserLoading: false,

    sid: '',
    interval: 0,
    timeRange: [null, null],

    courses: [],
    coursesLoading: false,
}

function rootReducer(state = initialState, action) {

    switch (action.type) {
        case GET_LOGIN: {
            return {
                ...state,
                userLoading: !state.userLogin
            }
        }
        case SET_LOGIN: {
            return {
                ...state,
                userLoading: false,
                browserLoading: false,
                userLogin: action.payload && "user" in action.payload ?
                    action.payload.user : state.userLogin,
                browserLogin: action.payload && "browser" in action.payload ?
                    action.payload.browser : state.browserLogin
            }
        }
        case REQUEST_USER_LOGIN: {
            return {
                ...state,
                userLoading: true
            }
        }
        case REQUEST_BROWSER_LOGIN: {
            return {
                ...state,
                browserLoading: true
            }
        }
        case SET_CONFIG: {
            const data = action.payload
            let sid = data.sid
            let timeRange = [null, null]

            let interval = parseInt(data.interval)
            if (data.start && data.end)
                timeRange = [moment(data.start, 'HHmm'), moment(data.end, 'HHmm')]
            return {
                ...state,
                sid: sid,
                interval: interval,
                timeRange: timeRange
            }
        }

        case GET_COURSES: {
            return {
                ...state,
                coursesLoading: true
            }
        }
        case SET_COURSES: {
            const courses = action.status === 'fail' ? [...state.courses] :
                action.payload.map(course => {
                    return {
                        ...course,
                        key: course.uid
                    }
                })

            return {
                ...state,
                coursesLoading: false,
                courses: courses
            }
        }

        case UPDATE_COURSE: {
            let course = {
                ...action.payload,
                key: action.payload.uid
            }
            let added = false
            const courses = state.courses.map((c) => {
                if (!added && c.uid === course.uid) {
                    added = true
                    return course
                }
                return c
            })

            if (!added) courses.push(course)

            return {
                ...state,
                coursesLoading: false,
                courses: courses
            }
        }
        case REMOVE_COURSES: {
            return {
                ...state,
                coursesLoading: false,
                courses: state.courses.filter((course) =>
                    action.payload.find(c => c.uid === course.uid)
                )
            }
        }
        default: {
            return state
        }
    }
}

export default rootReducer
